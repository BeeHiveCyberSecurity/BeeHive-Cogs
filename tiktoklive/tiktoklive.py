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
        self.config.register_guild(tiktok_users=[], alert_channel=None)
        self.clients = {}

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
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="TikTok Live Alert",
                        description=f"@{event.unique_id} is now live on TikTok!",
                        color=discord.Color.green()
                    )
                    await channel.send(embed=embed)

        self.bot.loop.create_task(self.check_loop(guild_id, client))

    async def check_loop(self, guild_id, client):
        while True:
            if not await client.is_live():
                client.logger.info("Client is currently not live. Checking again in 60 seconds.")
                await asyncio.sleep(60)
            else:
                client.logger.info("Requested client is live!")
                await client.connect()

    @commands.guild_only()
    @commands.group()
    async def tiktok(self, ctx):
        """TikTok live stream commands."""
        pass

    @commands.guild_only()
    @commands.group()
    async def tiktokset(self, ctx):
        """TikTok live stream settings commands."""
        pass

    @tiktokset.command()
    async def add(self, ctx, user: str):
        async with self.config.guild(ctx.guild).tiktok_users() as tiktok_users:
            if user not in tiktok_users:
                tiktok_users.append(user)
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
                    await ctx.send(f"Failed to add TikTok user {user}: {e}")
            else:
                await ctx.send(f"TikTok user {user} is already being followed.")

    @tiktokset.command()
    async def remove(self, ctx, user: str):
        async with self.config.guild(ctx.guild).tiktok_users() as tiktok_users:
            if user in tiktok_users:
                tiktok_users.remove(user)
                if ctx.guild.id in self.clients:
                    self.clients[ctx.guild.id] = [client for client in self.clients[ctx.guild.id] if client.unique_id != user]
                embed = discord.Embed(
                    title="TikTok User Removed",
                    description=f"TikTok user {user} removed for this server.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"TikTok user {user} is not being followed.")

    @tiktokset.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).alert_channel.set(channel.id)
        embed = discord.Embed(
            title="Alert Channel Set",
            description=f"Alert channel set to {channel.mention} for this server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @tiktok.command()
    async def check(self, ctx, user: str):
        guild_id = ctx.guild.id
        if guild_id in self.clients:
            for client in self.clients[guild_id]:
                if client.unique_id == user:
                    is_live = await client.is_live()
                    if is_live:
                        await ctx.send(f"TikTok user {user} is currently live!")
                    else:
                        await ctx.send(f"TikTok user {user} is not live at the moment.")
                    return
        await ctx.send(f"TikTok user {user} is not being followed in this server.")

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

