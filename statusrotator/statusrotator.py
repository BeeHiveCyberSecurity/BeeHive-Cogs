from redbot.core import commands, Config
import discord
import asyncio
import aiohttp
import json
from collections import deque
from datetime import datetime, timedelta

class StatusRotator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            antiphishing_status_enabled=False,
            blocked_domains_count=0
        )
        self.status_task = self.bot.loop.create_task(self.change_status())
        self.statuses = [
            lambda: f"Guarding {len(self.bot.guilds)} servers",
            lambda: f"Moderating {len(self.bot.users):,} users",
            self.get_message_count_status,
            self.get_uptime_status  # New status added here
        ]
        self.message_log = deque()
        self.bot.loop.create_task(self.load_settings())
        self.start_time = datetime.utcnow()  # Track bot start time

    async def load_settings(self):
        self.antiphishing_status_enabled = await self.config.antiphishing_status_enabled()
        self.blocked_domains_count = await self.config.blocked_domains_count()
        if self.antiphishing_status_enabled:
            await self.enable_antiphishing_status()

    def cog_unload(self):
        self.status_task.cancel()

    async def change_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for status in self.statuses:
                text = status()
                activity = discord.CustomActivity(name=text)
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(120)  # Change status every 120 seconds

    async def fetch_blocked_domains_count(self):
        url = "https://www.beehive.systems/hubfs/blocklist/blocklist.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list):
                                self.blocked_domains_count = len(data)
                            else:
                                print("Unexpected data format received from blocklist.")
                                self.blocked_domains_count = 0
                        except Exception as e:
                            print(f"Error parsing JSON from blocklist: {e}")
                            self.blocked_domains_count = 0
                    else:
                        print(f"Failed to fetch blocklist, status code: {response.status}")
                        self.blocked_domains_count = 0
            except aiohttp.ClientError as e:
                print(f"Client error while fetching blocklist: {e}")
                self.blocked_domains_count = 0
        await self.config.blocked_domains_count.set(self.blocked_domains_count)

    async def enable_antiphishing_status(self):
        await self.fetch_blocked_domains_count()
        self.statuses.append(lambda: f"Screening for {self.blocked_domains_count:,} bad domains")

    def get_message_count_status(self):
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        self.message_log = deque([timestamp for timestamp in self.message_log if timestamp > one_minute_ago])
        message_count = len(self.message_log)
        message_text = "message" if message_count == 1 else "messages"
        return f"Analyzing {message_count} {message_text} every minute"

    def get_uptime_status(self):
        now = datetime.utcnow()
        uptime = now - self.start_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"Online for {int(days)}d {int(hours)}h {int(minutes)}m"

    @commands.group()
    async def statusrotator(self, ctx):
        """StatusRotator command group"""
        pass

    @statusrotator.command()
    async def status(self, ctx):
        """Show what cog integrations are active"""
        antiphishing_status = "enabled" if self.antiphishing_status_enabled else "disabled"
        await ctx.send(f"Antiphishing status is {antiphishing_status}.")
        if self.antiphishing_status_enabled:
            await ctx.send(f"Blocked domains count: {self.blocked_domains_count}")

    @statusrotator.command()
    async def toggle(self, ctx, integration: str):
        """Toggle different integrations like antiphishing"""
        if integration.lower() == "antiphishing":
            self.antiphishing_status_enabled = not self.antiphishing_status_enabled
            await self.config.antiphishing_status_enabled.set(self.antiphishing_status_enabled)
            if self.antiphishing_status_enabled:
                self.bot.loop.create_task(self.enable_antiphishing_status())
                await ctx.send("Antiphishing status has been enabled.")
            else:
                self.statuses = [status for status in self.statuses if "bad domains" not in status()]
                await ctx.send("Antiphishing status has been disabled.")
        else:
            await ctx.send(f"Unknown integration: {integration}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self.message_log.append(datetime.utcnow())

    @commands.Cog.listener()
    async def on_ready(self):
        pass
