from redbot.core import commands, Config
import discord
import asyncio

class StatusRotator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.status_task = self.bot.loop.create_task(self.change_status())
        self.statuses = [
            lambda: f"Serving {len(self.bot.guilds)} servers",
            lambda: f"Serving {len(self.bot.users)} users",
            lambda: f"Uptime: {self.get_uptime()}",
        ]

    def cog_unload(self):
        self.status_task.cancel()

    async def change_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for status in self.statuses:
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name=status()))
                await asyncio.sleep(60)  # Change status every 60 seconds

    def get_uptime(self):
        delta = discord.utils.utcnow() - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = discord.utils.utcnow()

