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
        """Interact with the weather.gov API to fetch weather data via Discord"""

    @commands.guild_only()
    @weather.command(name="glossary")
    async def glossary(self, ctx, *, search_term: str = None):
        """Show a glossary, or specify a word to search"""
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

    @commands.guild_only()
    @weather.command(name="alerts")
    async def alerts(self, ctx):
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
        embed1 = discord.Embed(title="Summary of active weather alerts", color=0xfffffe)
        for key in ["total", "land", "marine"]:
            if key in data:
                embed1.add_field(name=key.capitalize(), value=data[key], inline=True)
        pages.append(embed1)

        # Page 2: regions
        embed2 = discord.Embed(title="Active weather alerts per region", color=0xfffffe)
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
                embed = discord.Embed(title="Active weather alerts per area", color=0xfffffe)
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
    
    @commands.guild_only()
    @weather.command(name="stations")
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
                for i in range(0, len(stations), 15):
                    embed = discord.Embed(
                        title="Weather observation stations", 
                        description=f"There are {len(stations)} stations in the coverage area", 
                        color=0xfffffe
                    )
                    for station in stations[i:i+15]:
                        station_name = station["properties"].get("name", "Unknown")
                        station_id = station["properties"].get("stationIdentifier", "Unknown")
                        coordinates = station["geometry"]["coordinates"] if "geometry" in station else ["Unknown", "Unknown"]
                        if coordinates != ["Unknown", "Unknown"]:
                            coordinates = [round(coordinates[0], 2), round(coordinates[1], 2)]
                        elevation = station["properties"].get("elevation", {}).get("value", "Unknown")
                        if elevation != "Unknown":
                            elevation = int(elevation)
                        time_zone = station["properties"].get("timeZone", "Unknown").replace("_", " ")
                        embed.add_field(
                            name=station_name, 
                            value=f"`{station_id}`\n`{coordinates[1]}, {coordinates[0]}`\n`{elevation} meters high`\n`{time_zone}`", 
                            inline=True
                        )
                    pages.append(embed)
                
                if not pages:
                    await ctx.send("No valid stations data found.")
                    return
                
                message = await ctx.send(embed=pages[0])
                await message.add_reaction("⬅️")
                await message.add_reaction("❌")
                await message.add_reaction("➡️")

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
    
    @commands.guild_only()
    @weather.command()
    async def radars(self, ctx):
        """Fetch and display radar stations information."""
        url = "https://api.weather.gov/radar/stations"
        headers = {"accept": "application/geo+json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch radar stations data.")
                    return
                data = await response.json()
        
        stations = data.get("features", [])
        if not stations:
            await ctx.send("No radar stations data found.")
            return
        
        pages = []
        for station in stations:
            station_name = station["properties"].get("name", "Unknown")
            station_id = station["properties"].get("stationIdentifier", "Unknown")
            coordinates = station["geometry"]["coordinates"] if "geometry" in station else ["Unknown", "Unknown"]
            if coordinates != ["Unknown", "Unknown"]:
                coordinates = [round(coordinates[0], 2), round(coordinates[1], 2)]
            elevation = station["properties"].get("elevation", {}).get("value", "Unknown")
            if elevation != "Unknown":
                elevation = int(elevation)
            time_zone = station["properties"].get("timeZone", "Unknown").replace("_", " ")
            
            rda_details = station["properties"].get("rda", None)
            latency = station["properties"].get("latency", "Unknown")
            if latency != "Unknown":
                current_value = latency['current']['value']
                average_value = latency['average']['value']
                max_value = latency['max']['value']
                level_two_last_received_time = discord.utils.format_dt(discord.utils.parse_time(latency['levelTwoLastReceivedTime']))
                max_latency_time = discord.utils.format_dt(discord.utils.parse_time(latency['maxLatencyTime']))
                reporting_host = latency['reportingHost']
                host = latency['host']
                
            description = f"Located at `{coordinates[1]}, {coordinates[0]}`, `{elevation} meters high` and operating in the `{time_zone}` timezone"

            embed = discord.Embed(title=f"{station_name} radar", description=description, color=0xfffffe)
            
            if rda_details is not None:
                embed.add_field(name="RDA Timestamp", value=rda_details.get("timestamp", "Unknown"), inline=True)
                embed.add_field(name="Reporting Host", value=rda_details.get("reportingHost", "Unknown"), inline=True)
                properties = rda_details.get("properties", {})
                embed.add_field(name="Resolution Version", value=properties.get("resolutionVersion", "Unknown"), inline=True)
                embed.add_field(name="NL2 Path", value=properties.get("nl2Path", "Unknown"), inline=True)
                embed.add_field(name="Volume Coverage Pattern", value=properties.get("volumeCoveragePattern", "Unknown"), inline=True)
                embed.add_field(name="Control Status", value=properties.get("controlStatus", "Unknown"), inline=True)
                embed.add_field(name="Build Number", value=properties.get("buildNumber", "Unknown"), inline=True)
                embed.add_field(name="Alarm Summary", value=properties.get("alarmSummary", "Unknown"), inline=True)
                embed.add_field(name="Mode", value=properties.get("mode", "Unknown"), inline=True)
                embed.add_field(name="Generator State", value=properties.get("generatorState", "Unknown"), inline=True)
                embed.add_field(name="Super Resolution Status", value=properties.get("superResolutionStatus", "Unknown"), inline=True)
                embed.add_field(name="Operability Status", value=properties.get("operabilityStatus", "Unknown"), inline=True)
                embed.add_field(name="Status", value=properties.get("status", "Unknown"), inline=True)
                avg_transmitter_power = properties.get("averageTransmitterPower", {})
                unit_code = avg_transmitter_power.get('unitCode', '').replace('wmoUnit:', '')
                embed.add_field(name="Average Transmitter Power", value=f"{avg_transmitter_power.get('value', 'Unknown')} {unit_code}", inline=True)
                reflectivity_calibration = properties.get("reflectivityCalibrationCorrection", {})
                unit_code = reflectivity_calibration.get('unitCode', '').replace('wmoUnit:', '')
                embed.add_field(name="Reflectivity Calibration Correction", value=f"{reflectivity_calibration.get('value', 'Unknown')} {unit_code}", inline=True)
            
            if latency != "Unknown":
                embed.add_field(name="Current Latency", value=current_value, inline=True)
                embed.add_field(name="Average Latency", value=average_value, inline=True)
                embed.add_field(name="Max Latency", value=max_value, inline=True)
                embed.add_field(name="Level Two Last Received Time", value=level_two_last_received_time, inline=True)
                embed.add_field(name="Max Latency Time", value=max_latency_time, inline=True)
                embed.add_field(name="Reporting Host", value=reporting_host, inline=True)
                embed.add_field(name="Host", value=host, inline=True)
            
            pages.append(embed)
        
        if not pages:
            await ctx.send("No valid radar stations data found.")
            return
        
        message = await ctx.send(embed=pages[0])
        await message.add_reaction("⬅️")
        await message.add_reaction("❌")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

        i = 0
        reaction = None
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
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
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

