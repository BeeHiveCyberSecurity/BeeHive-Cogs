from redbot.core import commands, Config
import aiohttp
from datetime import datetime as dt
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
            self.country_data = country_data

    def cog_unload(self):
        # Ensure the session is closed properly
        asyncio.create_task(self.session.close())

    @commands.group(name="holiday")
    async def holiday(self, ctx):
        """Group command for interacting with holidays."""

    @holiday.command(name="next")
    async def next(self, ctx):
        """Fetch the next public holiday."""
        country_code = await self.config.user(ctx.author).country_code()
        if not country_code:
            embed = discord.Embed(
                title="Country Code Not Set",
                description="You need to set your country code first using the `setcountry` command.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        current_year = dt.now().year
        async with self.session.get(f"https://date.nager.at/Api/v2/PublicHolidays/{current_year}/{country_code}") as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Failed to Fetch Holidays",
                    description="Failed to fetch holidays. Please try again later.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if data:
                # Filter out past holidays
                upcoming_holidays = [holiday for holiday in data if dt.strptime(holiday['date'], '%Y-%m-%d') >= dt.now()]
                if upcoming_holidays:
                    next_holiday = upcoming_holidays[0]
                    holiday_date = dt.strptime(next_holiday['date'], '%Y-%m-%d')
                    embed = discord.Embed(
                        title=f"Next {country_code} public holiday",
                        description=f"**{next_holiday['localName']}** occurring on **<t:{int(holiday_date.timestamp())}:D>** (**<t:{int(holiday_date.timestamp())}:R>**).",
                        color=0xfffffe
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="No upcoming holidays",
                        description=f"No upcoming public holidays found for {country_code}.",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="No upcoming holidays",
                    description=f"No upcoming public holidays found for {country_code}.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)

    @holiday.command(name="list")
    async def list(self, ctx):
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
                seen_holidays = set()
                embed = discord.Embed(
                    title=f"Public holidays in {country_code} for {ctx.message.created_at.year}",
                    color=0xfffffe
                )
                for holiday in data:
                    holiday_date = dt.strptime(holiday['date'], '%Y-%m-%d')
                    holiday_key = (holiday['localName'], holiday_date)
                    if holiday_key not in seen_holidays:
                        seen_holidays.add(holiday_key)
                        embed.add_field(
                            name=holiday['localName'],
                            value=f"**<t:{int(holiday_date.timestamp())}:D>** (**<t:{int(holiday_date.timestamp())}:R>**)",
                            inline=True
                        )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No public holidays found for {country_code} in {ctx.message.created_at.year}.")

    @commands.group(name="holidayset")
    async def holidayset(self, ctx):
        """Group command for interacting with holidays."""

    @holidayset.command(name="country")
    async def country(self, ctx, country_code: str):
        """Set your country code for fetching public holidays."""
        country_code = country_code.upper()
        if country_code not in self.valid_country_codes:
            await ctx.send(f"{country_code} is not a valid country code. Please provide a valid country code.")
            return
        
        country_name = next((country['name'] for country in self.country_data if country['countryCode'] == country_code), None)
        if not country_name:
            await ctx.send(f"{country_code} is not a valid country code. Please provide a valid country code.")
            return
        
        await self.config.user(ctx.author).country_code.set(country_code)
        
        embed = discord.Embed(
            title="Country Code Set",
            description=f"Your country code has been set to **{country_code}** ({country_name}).",
            color=0x2bbd8e
        )
        await ctx.send(embed=embed)

    @holiday.command(name="regions")
    async def regions(self, ctx):
        """Show a directory of all settable country codes and country names."""
        country_list = sorted(self.country_data, key=lambda x: x['name'])
        pages = [country_list[i:i + 15] for i in range(0, len(country_list), 15)]
        
        embeds = []
        for i, page in enumerate(pages):
            embed = discord.Embed(
                title=f"Country codes (Page {i + 1}/{len(pages)})",
                color=0xfffffe
            )
            for country in page:
                embed.add_field(
                    name=country['name'],
                    value=country['countryCode'],
                    inline=True
                )
            embeds.append(embed)
        
        message = await ctx.send(embed=embeds[0])
        if len(embeds) > 1:
            await self.paginate_embeds(ctx, message, embeds)

    async def paginate_embeds(self, ctx, message, embeds):
        current_page = 0
        await message.add_reaction("◀️")
        await message.add_reaction("❌")
        await message.add_reaction("▶️")
        

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️", "❌"] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "▶️" and current_page < len(embeds) - 1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "◀️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "❌":
                    await message.clear_reactions()
                    break
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
        await message.clear_reactions()
