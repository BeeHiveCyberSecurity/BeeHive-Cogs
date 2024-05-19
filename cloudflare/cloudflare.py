import discord
from redbot.core import commands, Config
import aiohttp

class Cloudflare(commands.Cog):
    """A Red-Discordbot cog to interact with the Cloudflare API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "api_key": None,
            "email": None,
        }
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession()

    @commands.group()
    async def cloudflare(self, ctx):
        """Cloudflare command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Cloudflare command passed.")

    @cloudflare.command()
    async def setapikey(self, ctx, api_key: str):
        """Set the Cloudflare API key."""
        await self.config.api_key.set(api_key)
        await ctx.send("Cloudflare API key set.")

    @cloudflare.command()
    async def setemail(self, ctx, email: str):
        """Set the Cloudflare account email."""
        await self.config.email.set(email)
        await ctx.send("Cloudflare email set.")

    @cloudflare.command()
    async def getzones(self, ctx):
        """Get the list of zones from Cloudflare."""
        api_key = await self.config.api_key()
        email = await self.config.email()
        if not api_key or not email:
            await ctx.send("API key or email not set.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get("https://api.cloudflare.com/client/v4/zones", headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch zones: {response.status}")
                return

            data = await response.json()
            zones = data.get("result", [])
            if not zones:
                await ctx.send("No zones found.")
                return

            zone_list = "\n".join([zone["name"] for zone in zones])
            await ctx.send(f"Zones:\n{zone_list}")

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
