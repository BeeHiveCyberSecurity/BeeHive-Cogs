import asyncio
from redbot.core import commands, Config #type: ignore
from TikTokLive import TikTokLiveClient #type: ignore
from TikTokLive.client.logger import LogLevel #type: ignore
from TikTokLive.events import ConnectEvent, CommentEvent #type: ignore
import discord #type: ignore
import logging
import yt_dlp
import os

class TikTokLiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(tiktok_user=None, alert_channel=None, alert_role=None, chat_log_channel=None)
        self.clients = {}
        self.live_status = {}  # Dictionary to keep track of live status
        self.chat_logs = {}  # Dictionary to store chat logs

    async def initialize_client(self, guild_id, user):
        client = TikTokLiveClient(unique_id=user)
        client.logger.setLevel(logging.INFO)  # Use logging.INFO instead of LogLevel.INFO
        self.clients[guild_id] = client

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
                        title="A creator just went live",
                        description=f"@{event.unique_id} is now live on TikTok!",
                        color=0x2bbd8e
                    )
                    view = discord.ui.View()
                    button = discord.ui.Button(
                        label="Watch now",
                        url=f"https://www.tiktok.com/@{event.unique_id}/live",
                        style=discord.ButtonStyle.url
                    )
                    view.add_item(button)
                    await channel.send(content=role_mention, embed=embed, view=view, allowed_mentions=discord.AllowedMentions(roles=True))

        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            if guild_id not in self.chat_logs:
                self.chat_logs[guild_id] = []
            self.chat_logs[guild_id].append(f"{event.user.uniqueId}: {event.comment}")

        self.bot.loop.create_task(self.check_loop(guild_id, client, user))
        self.bot.loop.create_task(self.chat_log_loop(guild_id, user))

    async def check_loop(self, guild_id, client, user):
        while True:
            try:
                is_live = await client.is_live()
                if not is_live:
                    client.logger.info("Client is currently not live. Checking again in 60 seconds.")
                    self.live_status[user] = False  # Update live status
                    await asyncio.sleep(90)
                else:
                    if not self.live_status.get(user, False):  # Only send alert if user was not previously live
                        client.logger.info("Requested client is live!")
                        await client.connect()
                        self.live_status[user] = True  # Update live status
                    else:
                        client.logger.info("Client is still live. No new alert sent.")
                    await asyncio.sleep(90)  # Check again in 60 seconds
            except Exception as e:
                client.logger.error(f"Error in check_loop: {e}")
                await asyncio.sleep(90)  # Wait before retrying

    async def chat_log_loop(self, guild_id, user):
        while True:
            await asyncio.sleep(30)
            if guild_id in self.chat_logs and self.chat_logs[guild_id]:
                chat_log_channel_id = await self.config.guild_from_id(guild_id).chat_log_channel()
                if chat_log_channel_id:
                    chat_log_channel = self.bot.get_channel(chat_log_channel_id)
                    if chat_log_channel:
                        chat_messages = "\n".join(self.chat_logs[guild_id])
                        embed = discord.Embed(
                            title=f"Recent chats for @{user}",
                            description=chat_messages,
                            color=discord.Color.blue()
                        )
                        await chat_log_channel.send(embed=embed)
                        self.chat_logs[guild_id] = []

    @commands.guild_only()
    @commands.group()
    async def tiktoklive(self, ctx):
        """TikTok live stream commands."""
        pass

    @commands.guild_only()
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def tiktokliveset(self, ctx):
        """TikTok live stream settings commands."""
        pass

    @tiktokliveset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def add(self, ctx, user: str):
        """Add a TikTok user to follow for live alerts."""
        tiktok_user = await self.config.guild(ctx.guild).tiktok_user()
        if tiktok_user is None:
            await self.config.guild(ctx.guild).tiktok_user.set(user)  # Save persistently
            try:
                await self.initialize_client(ctx.guild.id, user)
                embed = discord.Embed(
                    title="Creator followed",
                    description=f"TikTok user {user} added for this server.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await self.config.guild(ctx.guild).tiktok_user.set(None)  # Save persistently
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to add TikTok user {user}: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Creator already followed",
                description=f"TikTok user {tiktok_user} is already being followed. Remove them first to add a new user.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @tiktokliveset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def remove(self, ctx, user: str):
        """Remove a TikTok user from the follow list."""
        tiktok_user = await self.config.guild(ctx.guild).tiktok_user()
        if tiktok_user == user:
            await self.config.guild(ctx.guild).tiktok_user.set(None)  # Save persistently
            if ctx.guild.id in self.clients:
                await self.clients[ctx.guild.id].close()
                del self.clients[guild.id]
            embed = discord.Embed(
                title="Creator removed",
                description=f"TikTok user {user} removed for this server.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Creator not followed",
                description=f"TikTok user {user} is not being followed.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @tiktokliveset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the alert channel for TikTok live notifications."""
        await self.config.guild(ctx.guild).alert_channel.set(channel.id)
        embed = discord.Embed(
            title="Alert channel set",
            description=f"Alert channel set to {channel.mention} for this server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @tiktokliveset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def role(self, ctx, role: discord.Role):
        """Set the alert role for TikTok live notifications."""
        await self.config.guild(ctx.guild).alert_role.set(role.id)
        embed = discord.Embed(
            title="Alert/notification role set",
            description=f"Alert role set to {role.mention} for this server.",
            color=0x2bbd8e
        )
        await ctx.send(embed=embed)

    @tiktokliveset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def chatlog(self, ctx, channel: discord.TextChannel):
        """Set the chat log channel for TikTok live notifications."""
        await self.config.guild(ctx.guild).chat_log_channel.set(channel.id)
        embed = discord.Embed(
            title="Chat log set",
            description=f"Chat log channel set to {channel.mention} for this server.",
            color=0x2bbd8e
        )
        await ctx.send(embed=embed)

    @tiktokliveset.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def settings(self, ctx):
        """Show the current TikTok live stream settings."""
        guild_id = ctx.guild.id
        tiktok_user = await self.config.guild(ctx.guild).tiktok_user()
        alert_channel_id = await self.config.guild(ctx.guild).alert_channel()
        alert_role_id = await self.config.guild(ctx.guild).alert_role()
        chat_log_channel_id = await self.config.guild(ctx.guild).chat_log_channel()
        alert_channel = self.bot.get_channel(alert_channel_id) if alert_channel_id else None
        alert_role = ctx.guild.get_role(alert_role_id) if alert_role_id else None
        chat_log_channel = self.bot.get_channel(chat_log_channel_id) if chat_log_channel_id else None

        embed = discord.Embed(
            title="Current TikTok settings",
            color=0xfffffe
        )
        if tiktok_user:
            user_link = f"[{tiktok_user}](https://www.tiktok.com/@{tiktok_user})"
            embed.add_field(name="TikTok User", value=user_link, inline=False)
        else:
            embed.add_field(name="TikTok User", value="None", inline=False)
        embed.add_field(name="Alert Channel", value=alert_channel.mention if alert_channel else "None", inline=False)
        embed.add_field(name="Alert Role", value=alert_role.mention if alert_role else "None", inline=False)
        embed.add_field(name="Chat Log Channel", value=chat_log_channel.mention if chat_log_channel else "None", inline=False)

        await ctx.send(embed=embed)

    @tiktoklive.command()
    async def check(self, ctx, user: str):
        """Check if a TikTok user is currently live."""
        guild_id = ctx.guild.id
        if guild_id in self.clients and self.clients[guild_id].unique_id == user:
            client = self.clients[guild_id]
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
        else:
            embed = discord.Embed(
                title="User not followed",
                description=f"TikTok user {user} is not being followed in this server.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @tiktoklive.command()
    async def download(self, ctx, url: str):
        """Download a TikTok video and send it in the channel."""
        ydl_opts = {
            'format': 'best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',  # Use a temporary directory
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                video_title = info_dict.get('title', 'video')
                video_uploader = info_dict.get('uploader', 'unknown')
                video_duration = info_dict.get('duration', 0)
                video_path = ydl.prepare_filename(info_dict)
                
                embed = discord.Embed(
                    title="Downloaded successfully",
                    color=0x2bbd8e
                )
                embed.add_field(name="Title", value=video_title, inline=False)
                embed.add_field(name="Uploader", value=video_uploader, inline=False)
                embed.add_field(name="Duration", value=f"{video_duration} seconds", inline=False)
                
                await ctx.send(embed=embed, file=discord.File(video_path))
                os.remove(video_path)  # Clean up the downloaded file after sending
        except Exception as e:
            await ctx.send(f"Failed to download video: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        user = await self.config.guild(guild).tiktok_user()
        if user:
            await self.initialize_client(guild.id, user)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in self.clients:
            await self.clients[guild.id].close()
            del self.clients[guild.id]

