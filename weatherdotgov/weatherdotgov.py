import discord
from redbot.core import commands, Config
import aiohttp
import asyncio
import csv
from redbot.core.data_manager import bundled_data_path

class Weather(commands.Cog):
    """Weather information from weather.gov"""
    
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890)
        default_user = {
            "zip_code": None,
            "alerts": False  # Add alerts to default user config
        }
        self.config.register_user(**default_user)
        default_global = {
            "total_alerts_sent": 0,
            "nowcasts_fetched": 0,
            "forecasts_fetched": 0,
        }
        self.config.register_global(**default_global)
        data_dir = bundled_data_path(self)
        zip_code_file = (data_dir / "zipcodes.csv").open(mode="r")
        csv_reader = csv.reader(zip_code_file)
        self.zip_codes = {
            row[0]: (row[1], row[2])
            for i, row in enumerate(csv_reader)
            if i != 0
        }
        
    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def weatherset(self, ctx):
        """Set your weather preferences"""
        pass

    @weatherset.command(name="severealerts")
    async def severealerts(self, ctx, enable: bool):
        """Enable or disable weather alerts for your saved zip code"""
        user = ctx.author
        if enable:
            try:
                example_alert = discord.Embed(
                    title="Example Severe Thunderstorm Warning",
                    description="This is an example of a Severe Thunderstorm Warning to show you how alerts will look. Future alerts will not be examples, and you should listen to their guidance and instruction.",
                    color=0xff4545
                )
                example_alert.add_field(name="Description", value="Severe thunderstorms are occurring in your area.", inline=False)
                example_alert.add_field(name="Instruction", value="Take shelter immediately.", inline=False)
                example_alert.add_field(name="Severity", value="Severe", inline=True)
                example_alert.add_field(name="Urgency", value="Immediate", inline=True)
                example_alert.add_field(name="Certainty", value="Observed", inline=True)

                await user.send(embed=example_alert)
                await self.config.user(user).alerts.set(True)
                await ctx.send("Weather alerts have been enabled.")
            except discord.Forbidden:
                await ctx.send("I cannot send you direct messages. Please enable DMs from server members and try again.")
        else:
            await self.config.user(user).alerts.set(False)
            await ctx.send("Weather alerts have been disabled.")

    async def check_weather_alerts(self):
        """Check for weather alerts and DM users if any severe or extreme warnings are issued"""
        all_users = await self.config.all_users()
        users_with_alerts = [user_id for user_id, data in all_users.items() if data.get("alerts")]

        for user_id in users_with_alerts:
            user_data = await self.config.user_from_id(user_id).all()
            zip_code = user_data.get("zip_code")
            if not zip_code or zip_code not in self.zip_codes:
                continue

            latitude, longitude = self.zip_codes[zip_code]
            alerts_url = f"https://api.weather.gov/alerts/active?point={latitude.strip()},{longitude.strip()}"

            async with self.session.get(alerts_url) as response:
                if response.status != 200:
                    continue

                data = await response.json()
                alerts = data.get('features', [])
                severe_alerts = [alert for alert in alerts if alert['properties']['severity'] in ['Severe', 'Extreme']]

                if severe_alerts:
                    user = self.bot.get_user(user_id)
                    if user:
                        for alert in severe_alerts:
                            embed = discord.Embed(
                                title="Active weather alert for your location",
                                description=alert['properties']['headline'],
                                color=0xff4545
                            )
                            embed.add_field(name="Description", value=alert['properties']['description'], inline=False)
                            embed.add_field(name="Instruction", value=alert['properties']['instruction'], inline=False)
                            embed.add_field(name="Severity", value=alert['properties']['severity'], inline=True)
                            embed.add_field(name="Urgency", value=alert['properties']['urgency'], inline=True)
                            embed.add_field(name="Certainty", value=alert['properties']['certainty'], inline=True)
                            embed.set_footer(text=f"Issued by {alert['properties']['senderName']}")

                            await user.send(embed=embed)
                            total_alerts_sent = await self.config.total_alerts_sent()
                            await self.config.total_alerts_sent.set(total_alerts_sent + 1)

    async def start_alerts_task(self):
        while True:
            await self.check_weather_alerts()
            await asyncio.sleep(900)

    def cog_load(self):
        self.bot.loop.create_task(self.start_alerts_task())

    @weatherset.command(name="zip")
    async def zip(self, ctx, zip_code: str):
        """Save your zip code to the bot's config"""
        await self.config.user(ctx.author).zip_code.set(zip_code)
        await ctx.send(f"Your zip code has been set to `{zip_code}`. This is the location that will now be used in the future for your weather queries.")

    @weatherset.command(name="stats")
    async def stats(self, ctx):
        """Show statistics about weather feature usage"""
        all_users = await self.config.all_users()
        total_users = len(all_users)
        users_with_zip = sum(1 for user_data in all_users.values() if user_data.get("zip_code"))
        users_with_alerts = sum(1 for user_data in all_users.values() if user_data.get("alerts"))
        total_alerts_sent = await self.config.total_alerts_sent()
        nowcasts_fetched = await self.config.nowcasts_fetched()
        forecasts_fetched = await self.config.forecasts_fetched()

        embed = discord.Embed(
            title="Weather usage data",
            color=0xfffffe
        )
        embed.add_field(name="Total weather users", value=total_users, inline=True)
        embed.add_field(name="Zip codes currently saved", value=users_with_zip, inline=True)
        embed.add_field(name="Users with alerts enabled", value=users_with_alerts, inline=True)
        embed.add_field(name="Severe alerts dispatched", value=total_alerts_sent, inline=True)
        embed.add_field(name="Nowcasts provided", value=nowcasts_fetched, inline=True)
        embed.add_field(name="Forecasts provided", value=forecasts_fetched, inline=True)

        await ctx.send(embed=embed)


    @commands.group()
    async def weather(self, ctx):
        """Interact with the weather.gov API to fetch weather data via Discord"""
        pass

    @weather.command(name="now")
    async def now(self, ctx):
        """Fetch your current conditions and now-cast"""
        zip_code = await self.config.user(ctx.author).zip_code()
        if not zip_code:
            await ctx.send("You haven't set a zip code yet. Use the `weatherset zip` command to set one.")
            return
        
        # Fetch latitude and longitude using the zip code
        if zip_code not in self.zip_codes:
            await ctx.send("Invalid zip code. Please set a valid zip code.")
            return
        
        latitude, longitude = self.zip_codes[zip_code]
        points_url = f"https://api.weather.gov/points/{latitude.strip()},{longitude.strip()}"
        
        # Fetch weather data using the latitude and longitude
        async with self.session.get(points_url) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch the weather data. URL: {points_url}, Status Code: {response.status}")
                return

            data = await response.json()
            forecast_url = data.get('properties', {}).get('forecast')
            if not forecast_url:
                await ctx.send(f"Failed to retrieve forecast URL. URL: {points_url}, Data: {data}")
                return
            
            async with self.session.get(forecast_url) as forecast_response:
                if forecast_response.status != 200:
                    await ctx.send(f"Failed to fetch the forecast data. URL: {forecast_url}, Status Code: {forecast_response.status}")
                    return
                
                forecast_data = await forecast_response.json()
                periods = forecast_data.get('properties', {}).get('periods', [])
                if not periods:
                    await ctx.send(f"Failed to retrieve forecast periods. URL: {forecast_url}, Data: {forecast_data}")
                    return
                
                current_forecast = periods[0]
                detailed_forecast = current_forecast.get('detailedForecast', 'No detailed forecast available.')
                
                embed = discord.Embed(
                    title="Your current conditions",
                    description=detailed_forecast,
                    color=0xfffffe
                )
                embed.add_field(name="Temperature", value=f"{current_forecast.get('temperature', 'N/A')}°F")
                embed.add_field(name="Wind Speed", value=current_forecast.get('windSpeed', 'N/A'))
                embed.add_field(name="Wind Direction", value=current_forecast.get('windDirection', 'N/A'))
                
                await ctx.send(embed=embed)
                nowcasts_fetched = await self.config.nowcasts_fetched()
                await self.config.nowcasts_fetched.set(nowcasts_fetched + 1)

    @commands.guild_only()
    @weather.command(name="forecast")
    async def forecast(self, ctx):
        """Fetch your future forecast"""
        zip_code = await self.config.user(ctx.author).zip_code()
        if not zip_code:
            await ctx.send("You haven't set a zip code yet. Use the `weatherset zip` command to set one.")
            return
        
        # Fetch latitude and longitude using the zip code
        if zip_code not in self.zip_codes:
            await ctx.send("Invalid zip code. Please set a valid zip code.")
            return
        
        latitude, longitude = self.zip_codes[zip_code]
        points_url = f"https://api.weather.gov/points/{latitude.strip()},{longitude.strip()}"
        
        # Fetch weather data using the latitude and longitude
        async with self.session.get(points_url) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch the weather data. URL: {points_url}, Status Code: {response.status}")
                return

            data = await response.json()
            forecast_url = data.get('properties', {}).get('forecast')
            if not forecast_url:
                await ctx.send(f"Failed to retrieve forecast URL. URL: {points_url}, Data: {data}")
                return
            
            async with self.session.get(forecast_url) as forecast_response:
                if forecast_response.status != 200:
                    await ctx.send(f"Failed to fetch the forecast data. URL: {forecast_url}, Status Code: {forecast_response.status}")
                    return
                
                forecast_data = await forecast_response.json()
                periods = forecast_data.get('properties', {}).get('periods', [])
                if not periods:
                    await ctx.send(f"Failed to retrieve forecast periods. URL: {forecast_url}, Data: {forecast_data}")
                    return
                
                embeds = []
                
                for period in periods[:5]:  # Create a page for each of the next 5 forecast periods
                    name = period.get('name', 'N/A')
                    detailed_forecast = period.get('detailedForecast', 'No detailed forecast available.')
                    temperature = period.get('temperature', 'N/A')
                    if temperature != 'N/A':
                        temperature = f"{temperature}°F"
                    wind_speed = period.get('windSpeed', 'N/A')
                    wind_direction = period.get('windDirection', 'N/A')
                    
                    embed = discord.Embed(
                        title=f"Weather forecast for {name}",
                        description=f"{detailed_forecast}",
                        color=0xfffffe
                    )
                    embed.add_field(name="Temperature", value=temperature)
                    embed.add_field(name="Wind Speed", value=wind_speed)
                    embed.add_field(name="Wind Direction", value=wind_direction)
                    
                    embeds.append(embed)
                
                message = await ctx.send(embed=embeds[0])
                forecasts_fetched = await self.config.forecasts_fetched()
                await self.config.forecasts_fetched.set(forecasts_fetched + 1)
                page = 0
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")
                await message.add_reaction("❌")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                        if str(reaction.emoji) == "➡️":
                            page = (page + 1) % len(embeds)
                        elif str(reaction.emoji) == "⬅️":
                            page = (page - 1) % len(embeds)
                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break
                        
                        await message.edit(embed=embeds[page])
                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break


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
                host = latency['host']
                
            description = f"Located at `{coordinates[1]}, {coordinates[0]}`, `{elevation} meters high` and operating in the `{time_zone}` timezone"

            embed = discord.Embed(title=f"{station_name} radar", description=description, color=0xfffffe)
            
            if rda_details is not None:
                rda_timestamp = rda_details.get("timestamp", "Unknown")
                if rda_timestamp != "Unknown":
                    rda_timestamp = discord.utils.format_dt(discord.utils.parse_time(rda_timestamp))
                if rda_timestamp != "Unknown":
                    embed.add_field(name="RDA Timestamp", value=rda_timestamp, inline=True)
                reporting_host = rda_details.get('reportingHost', 'Unknown').upper()
                if reporting_host != "UNKNOWN":
                    embed.add_field(name="Reporting Host", value=f"`{reporting_host}`", inline=True)
                properties = rda_details.get("properties", {})
                resolution_version = properties.get('resolutionVersion', 'Unknown')
                if resolution_version != "Unknown":
                    embed.add_field(name="Resolution Version", value=f"`{resolution_version}`", inline=True)
                nl2_path = properties.get('nl2Path', 'Unknown')
                if nl2_path != "Unknown":
                    embed.add_field(name="NL2 Path", value=f"`{nl2_path}`", inline=True)
                volume_coverage_pattern = properties.get('volumeCoveragePattern', 'Unknown')
                if volume_coverage_pattern != "Unknown":
                    embed.add_field(name="Volume Coverage Pattern", value=f"`{volume_coverage_pattern}`", inline=True)
                control_status = properties.get('controlStatus', 'Unknown')
                if control_status != "Unknown":
                    embed.add_field(name="Control Status", value=f"`{control_status}`", inline=True)
                build_number = properties.get('buildNumber', 'Unknown')
                if build_number != "Unknown":
                    embed.add_field(name="Build Number", value=f"`{build_number}`", inline=True)
                alarm_summary = properties.get('alarmSummary', 'Unknown')
                if alarm_summary != "Unknown":
                    embed.add_field(name="Alarm Summary", value=f"`{alarm_summary}`", inline=True)
                mode = properties.get('mode', 'Unknown')
                if mode != "Unknown":
                    embed.add_field(name="Mode", value=f"`{mode}`", inline=True)
                generator_state = properties.get('generatorState', 'Unknown')
                if generator_state != "Unknown":
                    embed.add_field(name="Generator State", value=f"`{generator_state}`", inline=True)
                super_resolution_status = properties.get('superResolutionStatus', 'Unknown')
                if super_resolution_status != "Unknown":
                    embed.add_field(name="Super Resolution Status", value=f"`{super_resolution_status}`", inline=True)
                operability_status = properties.get('operabilityStatus', 'Unknown')
                if operability_status != "Unknown":
                    embed.add_field(name="Operability Status", value=f"`{operability_status}`", inline=True)
                status = properties.get('status', 'Unknown')
                if status != "Unknown":
                    embed.add_field(name="Status", value=f"`{status}`", inline=True)
                avg_transmitter_power = properties.get("averageTransmitterPower", {})
                avg_transmitter_power_value = avg_transmitter_power.get('value', 'Unknown')
                if avg_transmitter_power_value != "Unknown":
                    unit_code = avg_transmitter_power.get('unitCode', '').replace('wmoUnit:', '')
                    embed.add_field(name="Average Transmitter Power", value=f"`{avg_transmitter_power_value} {unit_code}`", inline=True)
                reflectivity_calibration = properties.get("reflectivityCalibrationCorrection", {})
                reflectivity_calibration_value = reflectivity_calibration.get('value', 'Unknown')
                if reflectivity_calibration_value != "Unknown":
                    unit_code = reflectivity_calibration.get('unitCode', '').replace('wmoUnit:', '')
                    embed.add_field(name="Reflectivity Calibration Correction", value=f"`{reflectivity_calibration_value} {unit_code}`", inline=True)
            
            if latency != "Unknown":
                embed.add_field(name="Current Latency", value=f"`{current_value} ms`", inline=True)
                embed.add_field(name="Average Latency", value=f"`{average_value} ms`", inline=True)
                embed.add_field(name="Max Latency", value=f"`{max_value} ms`", inline=True)
                embed.add_field(name="L2 Last Received Time", value=level_two_last_received_time, inline=True)
                embed.add_field(name="Max Latency Time", value=max_latency_time, inline=True)
                embed.add_field(name="Host", value=f"`{host.upper()}`", inline=True)
            
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

