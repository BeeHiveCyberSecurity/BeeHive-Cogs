import asyncio
from redbot.core import commands, Config
from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent
import discord

class TikTokLiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(tiktok_users=[], alert_channel=None)
        self.clients = {}

    async def initialize_client(self, guild_id, user):
        client = TikTokLiveClient(unique_id=user)
        client.logger.setLevel(LogLevel.INFO)
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
    @commands.command()
    async def add_tiktok_user(self, ctx, user: str):
        async with self.config.guild(ctx.guild).tiktok_users() as tiktok_users:
            if user not in tiktok_users:
                tiktok_users.append(user)
                await self.initialize_client(ctx.guild.id, user)
                embed = discord.Embed(
                    title="TikTok User Added",
                    description=f"TikTok user {user} added for this server.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"TikTok user {user} is already being followed.")

    @commands.guild_only()
    @commands.command()
    async def remove_tiktok_user(self, ctx, user: str):
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

    @commands.guild_only()
    @commands.command()
    async def set_alert_channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).alert_channel.set(channel.id)
        embed = discord.Embed(
            title="Alert Channel Set",
            description=f"Alert channel set to {channel.mention} for this server.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        users = await self.config.guild(guild).tiktok_users()
        for user in users:
            await self.initialize_client(guild.id, user)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in self.clients:
            for client in self.clients[guild.id]:
                await client.close()
            del self.clients[guild.id]

