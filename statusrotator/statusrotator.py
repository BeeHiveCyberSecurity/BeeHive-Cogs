from redbot.core import commands, Config #type: ignore
import discord #type: ignore
import asyncio
import aiohttp #type: ignore
from collections import deque
from datetime import datetime, timedelta
import re

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
            lambda: f"{len(self.bot.guilds)} guild{'s' if len(self.bot.guilds) == 1 else 's'} | {len(self.bot.users):,} user{'s' if len(self.bot.users) == 1 else 's'}" + (" | beehive.systems" if self.bot.user.id == 1152805502116429929 else ""),
            lambda: f"Watching over {len(self.bot.guilds)} server{'s' if len(self.bot.guilds) != 1 else ''}",
            lambda: f"Moderating {len(self.bot.users):,} user{'s' if len(self.bot.users) != 1 else ''}",
            self.get_message_count_status,
            self.get_uptime_status,
            self.get_latency_status,
            self.get_hyperlink_count_status  # New status for hyperlink count
        ]
        self.message_log = deque()
        self.hyperlink_log = deque()  # Log for hyperlinks
        self.bot.loop.create_task(self.load_settings())
        self.start_time = datetime.utcnow()
        self.presence_states = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
        self.current_presence_index = 0

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
                presence_state = self.presence_states[self.current_presence_index]
                await self.bot.change_presence(activity=activity, status=presence_state)
                self.current_presence_index = (self.current_presence_index + 1) % len(self.presence_states)
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

    def get_latency_status(self):
        latency = self.bot.latency * 1000  # Convert to milliseconds
        return f"Response latency {latency:.2f}ms"

    def get_hyperlink_count_status(self):
        now = datetime.utcnow()
        five_minutes_ago = now - timedelta(minutes=5)
        self.hyperlink_log = deque([timestamp for timestamp in self.hyperlink_log if timestamp > five_minutes_ago])
        hyperlink_count = len(self.hyperlink_log)
        hyperlink_text = "link" if hyperlink_count == 1 else "links"
        return f"Scanned {hyperlink_count} {hyperlink_text} in the last 5 minutes"

    @commands.group()
    async def statusrotator(self, ctx):
        """StatusRotator command group"""
        pass

    @statusrotator.command()
    @commands.has_permissions(administrator=True)
    async def status(self, ctx):
        """Show what cog integrations are active"""
        antiphishing_status = "enabled" if self.antiphishing_status_enabled else "disabled"
        embed = discord.Embed(title="StatusRotator Integrations", color=discord.Color.blue())
        embed.add_field(name="Antiphishing Status", value=antiphishing_status, inline=False)
        if self.antiphishing_status_enabled:
            embed.add_field(name="Blocked Domains Count", value=str(self.blocked_domains_count), inline=False)
        await ctx.send(embed=embed)

    @statusrotator.command()
    @commands.has_permissions(administrator=True)
    async def toggle(self, ctx, integration: str):
        """Toggle different integrations like antiphishing"""
        if integration.lower() == "antiphishing":
            self.antiphishing_status_enabled = not self.antiphishing_status_enabled
            await self.config.antiphishing_status_enabled.set(self.antiphishing_status_enabled)
            if self.antiphishing_status_enabled:
                self.bot.loop.create_task(self.enable_antiphishing_status())
                embed = discord.Embed(description="Antiphishing status has been enabled.", color=0x2bbd8e)
                await ctx.send(embed=embed)
            else:
                self.statuses = [status for status in self.statuses if "bad domains" not in status()]
                embed = discord.Embed(description="Antiphishing status has been disabled.", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"Unknown integration: {integration}", color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self.message_log.append(datetime.utcnow())
        # Check for hyperlinks in the message
        if re.search(r'http[s]?://', message.content):
            self.hyperlink_log.append(datetime.utcnow())

    @commands.Cog.listener()
    async def on_ready(self):
        pass
