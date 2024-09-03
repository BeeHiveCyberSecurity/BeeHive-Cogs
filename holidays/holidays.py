from redbot.core import commands, Config
import aiohttp
import discord
import asyncio
import json
from redbot.core.data_manager import bundled_data_path

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
        
        # Load valid country codes from the JSON file
        data_dir = bundled_data_path(self)
        with (data_dir / "country_codes.json").open(mode="r") as f:
            country_data = json.load(f)
            self.valid_country_codes = {entry["countryCode"] for entry in country_data}

    def cog_unload(self):
        # Ensure the session is closed properly
        asyncio.create_task(self.session.close())

    @commands.group(name="holidays")
    async def holidays(self, ctx):
        """Group command for interacting with holidays."""

    @holidays.command(name="next")
    async def holidays_next(self, ctx):
        """Fetch the next public holiday."""
        country_code = await self.config.user(ctx.author).country_code()
        if not country_code:
            await ctx.send("You need to set your country code first using the `setcountry` command.")
            return

        async with self.session.get(f"https://date.nager.at/Api/v2/NextPublicHolidaysWorldwide") as response:
            if response.status != 200:
                await ctx.send("Failed to fetch holidays. Please try again later.")
                return

            data = await response.json()
            next_holiday = next((holiday for holiday in data if holiday["countryCode"] == country_code), None)
            if next_holiday:
                await ctx.send(f"The next public holiday in {country_code} is {next_holiday['localName']} on {next_holiday['date']}.")
            else:
                await ctx.send(f"No upcoming public holidays found for {country_code}.")

    @holidays.command(name="list")
    async def holidays_list(self, ctx):
        """List all public holidays for the current year."""
        country_code = await self.config.user(ctx.author).country_code()
        if not country_code:
            await ctx.send("You need to set your country code first using the `setcountry` command.")
            return

        async with self.session.get(f"https://date.nager.at/Api/v2/PublicHolidays/{ctx.message.created_at.year}/{country_code}") as response:
            if response.status != 200:
                await ctx.send("Failed to fetch holidays. Please try again later.")
                return

            data = await response.json()
            if data:
                embed = discord.Embed(
                    title=f"Public holidays in {country_code} for {ctx.message.created_at.year}",
                    color=discord.Color.blue()
                )
                for holiday in data:
                    embed.add_field(
                        name=holiday['localName'],
                        value=f"<t:{int(datetime.strptime(holiday['date'], '%Y-%m-%d').timestamp())}:D>",
                        inline=True
                    )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No public holidays found for {country_code} in {ctx.message.created_at.year}.")

    @holidays.command(name="setcountry")
    async def set_country(self, ctx, country_code: str):
        """Set your country code for fetching public holidays."""
        country_code = country_code.upper()
        if country_code not in self.valid_country_codes:
            await ctx.send(f"{country_code} is not a valid country code. Please provide a valid country code.")
            return
        
        await self.config.user(ctx.author).country_code.set(country_code)
        await ctx.send(f"Your country code has been set to {country_code}.")
