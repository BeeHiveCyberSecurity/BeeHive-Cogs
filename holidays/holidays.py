from redbot.core import commands, Config
import aiohttp
import asyncio

class Holidays(commands.Cog):
    """Cog to interact with the Nager.Date API to fetch public holidays."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_user = {
            "country_code": None
        }
        self.config.register_user(**default_user)

    def cog_unload(self):
        # Ensure the session is closed properly
        asyncio.create_task(self.session.close())

    @commands.command(name="setcountry")
    async def set_country(self, ctx, country_code: str):
        """Set your country code for fetching public holidays."""
        await self.config.user(ctx.author).country_code.set(country_code.upper())
        await ctx.send(f"Your country code has been set to {country_code.upper()}.")

