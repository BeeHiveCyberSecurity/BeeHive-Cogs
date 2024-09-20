from redbot.core import commands, Config
import discord
import asyncio
import aiohttp

class StatusRotator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.status_task = self.bot.loop.create_task(self.change_status())
        self.statuses = [
            ("watching", lambda: f"over {len(self.bot.guilds)} servers"),
            ("watching", lambda: f"over {len(self.bot.users)} users"),
        ]
        self.blocked_domains_count = 0
        self.antiphishing_enabled = "antiphishing" in bot.cogs

        if self.antiphishing_enabled:
            self.bot.loop.create_task(self.enable_antiphishing_on_startup())

    def cog_unload(self):
        self.status_task.cancel()

    async def change_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for activity_type, status in self.statuses:
                if activity_type == "watching":
                    activity = discord.Activity(type=discord.ActivityType.watching, name=status())
                elif activity_type == "listening":
                    activity = discord.Activity(type=discord.ActivityType.listening, name=status())
                elif activity_type == "playing":
                    activity = discord.Game(name=status())
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(120)  # Change status every 120 seconds

    async def fetch_blocked_domains_count(self):
        url = "https://www.beehive.systems/hubfs/blocklist/blocklist.json"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            self.blocked_domains_count = len(data)
                        else:
                            self.blocked_domains_count = 0
                    else:
                        self.blocked_domains_count = 0
            except aiohttp.ClientError:
                self.blocked_domains_count = 0

    async def enable_antiphishing_on_startup(self):
        await self.fetch_blocked_domains_count()
        self.statuses.append(("watching", lambda: f"for {self.blocked_domains_count} bad domains"))

    @commands.group()
    async def statusrotator(self, ctx):
        """StatusRotator command group"""
        pass

    @statusrotator.command()
    async def status(self, ctx):
        """Show what cog integrations are active"""
        antiphishing_status = "enabled" if self.antiphishing_enabled else "disabled"
        await ctx.send(f"Antiphishing integration is {antiphishing_status}.")

    @statusrotator.command()
    async def toggle(self, ctx, integration: str):
        """Toggle different integrations like antiphishing"""
        if integration.lower() == "antiphishing":
            self.antiphishing_enabled = not self.antiphishing_enabled
            if self.antiphishing_enabled:
                self.bot.loop.create_task(self.enable_antiphishing_on_startup())
                await ctx.send("Antiphishing integration has been enabled.")
            else:
                self.statuses = [status for status in self.statuses if "bad domains" not in status[1]()]
                await ctx.send("Antiphishing integration has been disabled.")
        else:
            await ctx.send(f"Unknown integration: {integration}")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

