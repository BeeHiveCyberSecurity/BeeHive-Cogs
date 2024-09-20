import asyncio
from redbot.core import commands, Config
from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent
import discord
import logging

class TikTokLiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(tiktok_users=[], alert_channel=None, alert_role=None)
        self.clients = {}
        self.live_status = {}  # Dictionary to keep track of live status

    async def initialize_client(self, guild_id, user):
        client = TikTokLiveClient(unique_id=user)
        client.logger.setLevel(logging.INFO)  # Use logging.INFO instead of LogLevel.INFO
        if guild_id not in self.clients:
            self.clients[guild_id] = []
        self.clients[guild_id].append(client)

        @client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            client.logger.info(f"Connected to @{event.unique_id}!")
            channel_id = await self.config.guild_from_id(guild_id).alert_channel()
            role_id = await self.config.guild_from_id(guild_id).alert_role()
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    role_mention = f"<@&{role_id}>" if role_id else ""
                    embed = discord.Embed(
                        title="TikTok Live Alert",
                        description=f"@{event.unique_id} is now live on TikTok!",
                        color=discord.Color.green()
                    )
                    await channel.send(content=role_mention, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

        self.bot.loop.create_task(self.check_loop(guild_id, client, user))

    async def check_loop(self, guild_id, client, user):
        while True:
            try:
                is_live = await client.is_live()
                if not is_live:
                    client.logger.info("Client is currently not live. Checking again in 60 seconds.")
                    self.live_status[user] = False  # Update live status
                    await asyncio.sleep(60)
                else:
                    if not self.live_status.get(user, False):  # Only send alert if user was not previously live
                        client.logger.info("Requested client is live!")
                        await client.connect()
                        self.live_status[user] = True  # Update live status
                    else:
                        client.logger.info("Client is still live. No new alert sent.")
                    await asyncio.sleep(60)  # Check again in 60 seconds
            except Exception as e:
                client.logger.error(f"Error in check_loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    @commands.guild_only()
    @commands.group()
    async def tiktok(self, ctx):
        """TikTok live stream commands."""
        pass

    @commands.guild_only()
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def tiktokset(self, ctx):
        """TikTok live stream settings commands."""
        pass

    @tiktokset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def add(self, ctx, user: str):
        async with self.config.guild(ctx.guild).tiktok_users() as tiktok_users:
            if user not in tiktok_users:
                tiktok_users.append(user)
                await self.config.guild(ctx.guild).tiktok_users.set(tiktok_users)  # Save persistently
                try:
                    await self.initialize_client(ctx.guild.id, user)
                    embed = discord.Embed(
                        title="TikTok User Added",
                        description=f"TikTok user {user} added for this server.",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
                except Exception as e:
                    tiktok_users.remove(user)
                    await self.config.guild(ctx.guild).tiktok_users.set(tiktok_users)  # Save persistently
                    embed = discord.Embed(
                        title="Error",
                        description=f"Failed to add TikTok user {user}: {e}",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="User Already Followed",
                    description=f"TikTok user {user} is already being followed.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)

    @tiktokset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def remove(self, ctx, user: str):
        async with self.config.guild(ctx.guild).tiktok_users() as tiktok_users:
            if user in tiktok_users:
                tiktok_users.remove(user)
                await self.config.guild(ctx.guild).tiktok_users.set(tiktok_users)  # Save persistently
                if ctx.guild.id in self.clients:
                    self.clients[ctx.guild.id] = [client for client in self.clients[ctx.guild.id] if client.unique_id != user]
                embed = discord.Embed(
                    title="TikTok User Removed",
                    description=f"TikTok user {user} removed for this server.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="User Not Followed",
                    description=f"TikTok user {user} is not being followed.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)

    @tiktokset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).alert_channel.set(channel.id)
        embed = discord.Embed(
            title="Alert Channel Set",
            description=f"Alert channel set to {channel.mention} for this server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @tiktokset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def role(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).alert_role.set(role.id)
        embed = discord.Embed(
            title="Alert Role Set",
            description=f"Alert role set to {role.mention} for this server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @tiktokset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def settings(self, ctx):
        guild_id = ctx.guild.id
        tiktok_users = await self.config.guild(ctx.guild).tiktok_users()
        alert_channel_id = await self.config.guild(ctx.guild).alert_channel()
        alert_role_id = await self.config.guild(ctx.guild).alert_role()
        alert_channel = self.bot.get_channel(alert_channel_id) if alert_channel_id else None
        alert_role = ctx.guild.get_role(alert_role_id) if alert_role_id else None

        embed = discord.Embed(
            title="Current TikTok Settings",
            color=discord.Color.blue()
        )
        embed.add_field(name="TikTok Users", value=", ".join(tiktok_users) if tiktok_users else "None", inline=False)
        embed.add_field(name="Alert Channel", value=alert_channel.mention if alert_channel else "None", inline=False)
        embed.add_field(name="Alert Role", value=alert_role.mention if alert_role else "None", inline=False)

        await ctx.send(embed=embed)

    @tiktok.command()
    async def check(self, ctx, user: str):
        guild_id = ctx.guild.id
        if guild_id in self.clients:
            for client in self.clients[guild_id]:
                if client.unique_id == user:
                    is_live = await client.is_live()
                    if is_live:
                        embed = discord.Embed(
                            title="User Live",
                            description=f"TikTok user {user} is currently live!",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title="User Not Live",
                            description=f"TikTok user {user} is not live at the moment.",
                            color=discord.Color.orange()
                        )
                        await ctx.send(embed=embed)
                    return
        embed = discord.Embed(
            title="User not followed",
            description=f"TikTok user {user} is not being followed in this server.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        users = await self.config.guild(guild).tiktok_users()
        for user in users:
            await self.initialize_client(guild.id, user)
            await asyncio.sleep(5)  # Wait 5 seconds between initializing clients to avoid rate limiting

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in self.clients:
            for client in self.clients[guild.id]:
                await client.close()
            del self.clients[guild.id]

