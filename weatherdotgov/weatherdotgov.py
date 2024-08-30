import discord
from redbot.core import commands
import aiohttp
import asyncio

class Weather(commands.Cog):
    """Weather information from weather.gov"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def weather(self, ctx):
        """Weather command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand for weather.")

    @weather.command(name="glossary")
    async def glossary(self, ctx, *, search_term: str = None):
        """Fetch and display the weather glossary from weather.gov"""
        headers = {"Accept": "application/ld+json"}
        async with self.session.get("https://api.weather.gov/glossary", headers=headers) as response:
            if response.status != 200:
                await ctx.send("Failed to fetch the glossary. Please try again later.")
                return

            data = await response.json()
            terms = data.get("glossary", [])

            if not terms:
                await ctx.send("No glossary terms found.")
                return

            if search_term:
                terms = [term for term in terms if term.get("term") and search_term.lower() in term.get("term", "").lower()]

            if not terms:
                await ctx.send(f"No glossary terms found for '{search_term}'.")
                return

            def html_to_markdown(html):
                """Convert HTML to Markdown"""
                replacements = {
                    "<b>": "**", "</b>": "**",
                    "<i>": "*", "</i>": "*",
                    "<strong>": "**", "</strong>": "**",
                    "<em>": "*", "</em>": "*",
                    "<br>": "\n", "<br/>": "\n", "<br />": "\n",
                    "<p>": "\n", "</p>": "\n",
                    "<ul>": "\n", "</ul>": "\n",
                    "<li>": "- ", "</li>": "\n",
                    "<h1>": "# ", "</h1>": "\n",
                    "<h2>": "## ", "</h2>": "\n",
                    "<h3>": "### ", "</h3>": "\n",
                    "<h4>": "#### ", "</h4>": "\n",
                    "<h5>": "##### ", "</h5>": "\n",
                    "<h6>": "###### ", "</h6>": "\n",
                }
                for html_tag, markdown in replacements.items():
                    html = html.replace(html_tag, markdown)
                return html

            pages = []
            for term in terms:
                word = term.get("term", "No title")
                description = term.get("definition", "No description")
                if word is None or description is None:  # Ignore terms or descriptions that are "null"
                    continue
                if not description:  # Ensure description is not empty
                    description = "No description available."
                description = html_to_markdown(description)
                embed = discord.Embed(title=word, description=description, color=0x1E90FF)
                pages.append(embed)

            if not pages:
                await ctx.send("No valid glossary terms found.")
                return

            message = await ctx.send(embed=pages[0])
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            await message.add_reaction("❌")  # Add a close reaction

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

            i = 0
            reaction = None
            while True:
                if str(reaction) == "⬅️":
                    if i > 0:
                        i -= 1
                        await message.edit(embed=pages[i])
                elif str(reaction) == "➡️":
                    if i < len(pages) - 1:
                        i += 1
                        await message.edit(embed=pages[i])
                elif str(reaction) == "❌":
                    await message.delete()
                    break
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break

    @weather.command(name="alertsummary")
    async def alertsummary(self, ctx):
        """Shows a statistical summary of active weather alerts"""
        url = "https://api.weather.gov/alerts/active/count"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch active alerts.")
                    return
                data = await response.json()
                    
        pages = []

        # Page 1: total, land, marine
        embed1 = discord.Embed(title="Summary of active weather alerts", color=0x1E90FF)
        for key in ["total", "land", "marine"]:
            if key in data:
                embed1.add_field(name=key.capitalize(), value=data[key], inline=True)
        pages.append(embed1)

        # Page 2: regions
        embed2 = discord.Embed(title="Active weather alerts per region", color=0x1E90FF)
        region_full_names = {
            "AL": "Alaska", "AT": "Atlantic", "GL": "Great Lakes", "GM": "Gulf of Mexico",
            "PA": "Pacific", "PI": "Pacific Islands"
        }
        if "regions" in data:
            for region, count in data["regions"].items():
                full_name = region_full_names.get(region, region)
                embed2.add_field(name=full_name, value=count, inline=True)
        pages.append(embed2)

        # Page 3 and beyond: areas
        state_full_names = {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
            "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
            "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
            "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
            "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
            "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
            "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
            "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
            "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
            "AM": "Atlantic Ocean", "GM": "Gulf of Mexico", "LE": "Lake Erie", "LH": "Lake Huron",
            "LM": "Lake Michigan", "LO": "Lake Ontario", "LS": "Lake Superior", "PH": "Pacific Ocean (Hawaii)",
            "PK": "Pacific Ocean (Alaska)", "PS": "Pacific Ocean (California)", "PZ": "Pacific Ocean (Washington)",
            "LC": "Lake Champlain", "PM": "Puerto Rico (Marine)", "PR": "Puerto Rico (Land)", "VI": "Virgin Islands"
        }

        if "areas" in data:
            states = list(data["areas"].items())
            for i in range(0, len(states), 25):
                embed = discord.Embed(title="Active weather alerts per area", color=0x1E90FF)
                for state, count in states[i:i+25]:
                    full_name = state_full_names.get(state, state)
                    embed.add_field(name=full_name, value=count, inline=True)
                pages.append(embed)

        if not pages:
            await ctx.send("No valid alert data found.")
            return

        message = await ctx.send(embed=pages[0])
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        await message.add_reaction("❌")  # Add a close reaction

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

        i = 0
        reaction = None
        while True:
            if str(reaction) == "⬅️":
                if i > 0:
                    i -= 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == "➡️":
                if i < len(pages) - 1:
                    i += 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == "❌":
                await message.delete()
                break
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    @weather.command()
    async def stations(self, ctx):
        """Fetch and display weather observation stations."""
        url = "https://api.weather.gov/stations"
        headers = {"accept": "application/geo+json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch stations data.")
                    return
                data = await response.json()
                
                stations = data.get("features", [])
                if not stations:
                    await ctx.send("No stations data found.")
                    return
                
                pages = []
                for i in range(0, len(stations), 10):
                    embed = discord.Embed(title="Weather Observation Stations", color=0x1E90FF)
                    for station in stations[i:i+10]:
                        station_name = station["properties"].get("name", "Unknown")
                        station_id = station["properties"].get("stationIdentifier", "Unknown")
                        embed.add_field(name=station_name, value=f"ID: {station_id}", inline=True)
                    pages.append(embed)
                
                if not pages:
                    await ctx.send("No valid stations data found.")
                    return
                
                message = await ctx.send(embed=pages[0])
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")
                await message.add_reaction("❌")  # Add a close reaction

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

                i = 0
                reaction = None
                while True:
                    if str(reaction) == "⬅️":
                        if i > 0:
                            i -= 1
                            await message.edit(embed=pages[i])
                    elif str(reaction) == "➡️":
                        if i < len(pages) - 1:
                            i += 1
                            await message.edit(embed=pages[i])
                    elif str(reaction) == "❌":
                        await message.delete()
                        break
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break



