import discord #type: ignore
import aiohttp #type: ignore
import asyncio
import csv
from datetime import datetime
from redbot.core import commands, Config #type: ignore
from redbot.core.data_manager import bundled_data_path #type: ignore

class Weather(commands.Cog):
    """Weather.gov is the official website of the National Weather Service (NWS), a U.S. government agency responsible for providing weather, water, and climate data, forecasts, and warnings. It offers accurate and timely information on weather conditions, alerts for severe weather events, and climate-related updates to help the public stay informed and safe."""
    
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890)
        default_user = {
            "zip_code": None,
            "severealerts": False,
            "freezealerts": False,
            "heatalerts": False,
        }
        self.config.register_user(**default_user)
        default_global = {
            "total_alerts_sent": 0,
            "total_heat_alerts_sent": 0,
            "total_freeze_alerts_sent": 0,
            "nowcasts_fetched": 0,
            "forecasts_fetched": 0,
            "glossary_definitions_shown": 0,
        }
        self.config.register_global(**default_global)
        data_dir = bundled_data_path(self)
        with (data_dir / "zipcodes.csv").open(mode="r") as zip_code_file:
            csv_reader = csv.reader(zip_code_file)
            self.zip_codes = {
                row[0]: (row[1], row[2])
                for i, row in enumerate(csv_reader)
                if i != 0
            }
        
    def cog_load(self):
        self.bot.loop.create_task(self.start_severe_alerts_task())
        self.bot.loop.create_task(self.start_freeze_alerts_task())
        self.bot.loop.create_task(self.start_heat_alerts_task())

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def weather(self, ctx):
        """Fetch current and upcoming conditions, search and explore hundreds of weather-focused words, check alert statistics across the country, and fetch information on observation stations and radar installations"""

    @weather.command(name="stats")
    async def stats(self, ctx):
        """Show statistics about weather feature usage"""
        all_users = await self.config.all_users()
        users_with_zip = sum(1 for user_data in all_users.values() if user_data.get("zip_code"))
        users_with_severe_alerts = sum(1 for user_data in all_users.values() if user_data.get("severealerts"))
        users_with_freeze_alerts = sum(1 for user_data in all_users.values() if user_data.get("freezealerts"))
        users_with_heat_alerts = sum(1 for user_data in all_users.values() if user_data.get("heatalerts"))
        total_alerts_sent = await self.config.total_alerts_sent()
        heat_alerts_sent = await self.config.total_heat_alerts_sent()
        cold_alerts_sent = await self.config.total_freeze_alerts_sent()
        nowcasts_fetched = await self.config.nowcasts_fetched()
        forecasts_fetched = await self.config.forecasts_fetched()
        glossary_definitions_shown = await self.config.glossary_definitions_shown()

        embed = discord.Embed(
            title="Weather usage data",
            description="Data aggregated from global usage of bot",
            color=0xfffffe
        )
        embed.add_field(name="Zip codes stored", value=f"{users_with_zip} zip code{'s' if users_with_zip != 1 else ''}", inline=True)
        embed.add_field(name="Severe alert subscribers", value=f"{users_with_severe_alerts} subscriber{'s' if users_with_severe_alerts != 1 else ''}", inline=True)
        embed.add_field(name="Freeze alert subscribers", value=f"{users_with_freeze_alerts} subscriber{'s' if users_with_freeze_alerts != 1 else ''}", inline=True)
        embed.add_field(name="Heat alert subscribers", value=f"{users_with_heat_alerts} subscriber{'s' if users_with_heat_alerts != 1 else ''}", inline=True)
        embed.add_field(name="Severe alerts sent", value=f"{total_alerts_sent} alert{'s' if total_alerts_sent != 1 else ''}", inline=True)
        embed.add_field(name="Cold alerts sent", value=f"{cold_alerts_sent} alert{'s' if cold_alerts_sent != 1 else ''}", inline=True)
        embed.add_field(name="Heat alerts sent", value=f"{heat_alerts_sent} alert{'s' if heat_alerts_sent != 1 else ''}", inline=True)
        embed.add_field(name="Nowcasts served", value=f"{nowcasts_fetched} nowcast{'s' if nowcasts_fetched != 1 else ''}", inline=True)
        embed.add_field(name="Forecasts served", value=f"{forecasts_fetched} forecast{'s' if forecasts_fetched != 1 else ''}", inline=True)
        embed.add_field(name="Glossary terms shown", value=f"{glossary_definitions_shown} term{'s' if glossary_definitions_shown != 1 else ''}", inline=True)      

        await ctx.send(embed=embed)

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
        
        # Fetch current weather data using the latitude and longitude
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": str(latitude).strip(),
            "longitude": str(longitude).strip(),
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "hourly": "uv_index,cape,direct_radiation_instant,soil_temperature_0cm",
            "minutely_15": "lightning_potential,visibility,soil_moisture_0_to_1cm",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_hours": 1,
            "forecast_minutely_15": 1
        }
        
        queryString = "&".join(f"{key}={value}" for key, value in params.items())
        weather_url = f"{url}?{queryString}"
        
        async with self.session.get(weather_url) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch the weather data. URL: {weather_url}, Status Code: {response.status}")
                return

            data = await response.json()
            if not data:
                await ctx.send(f"Failed to retrieve current weather data. URL: {weather_url}, Data: {data}")
                return
            
            current = data.get('current', {})
            hourly = data.get('hourly', {})
            minutely_15 = data.get('minutely_15', {})
            
            embed = discord.Embed(
                title="Your current conditions",
                color=0xfffffe
            )
            embed.add_field(name="Temperature", value=f"{current.get('temperature_2m', 'N/A')}°F")
            embed.add_field(name="Feels like", value=f"{current.get('apparent_temperature', 'N/A')}°F")

            ground_temp = hourly.get('soil_temperature_0cm', 'N/A')
            if isinstance(ground_temp, list) and ground_temp:
                ground_temp = ground_temp[0]
            embed.add_field(name="Ground temperature", value=f"{ground_temp}°F")
            
            embed.add_field(name="Humidity", value=f"{current.get('relative_humidity_2m', 'N/A')}%")
            precipitation = current.get('precipitation', 'N/A')
            if precipitation != 'N/A' and precipitation != 0.0:
                embed.add_field(name="Precipitation", value=f"{precipitation} inches")
            
            rain = current.get('rain', 'N/A')
            if rain != 'N/A' and rain != 0.0:
                embed.add_field(name="Rain", value=f"{rain} inches")
            
            showers = current.get('showers', 'N/A')
            if showers != 'N/A' and showers != 0.0:
                embed.add_field(name="Showers", value=f"{showers} inches")
            
            snowfall = current.get('snowfall', 'N/A')
            if snowfall != 'N/A' and snowfall != 0.0:
                embed.add_field(name="Snowfall", value=f"{snowfall} inches")
            
            embed.add_field(name="Cloud cover", value=f"{current.get('cloud_cover', 'N/A')}%")
            embed.add_field(name="Pressure (MSL)", value=f"{current.get('pressure_msl', 'N/A')} hPa")
            embed.add_field(name="Surface pressure", value=f"{current.get('surface_pressure', 'N/A')} hPa")
            embed.add_field(name="Wind speed", value=f"{current.get('wind_speed_10m', 'N/A')} mph")
            wind_direction = current.get('wind_direction_10m', 'N/A')
            if wind_direction != 'N/A':
                if (wind_direction >= 0 and wind_direction <= 22.5) or (wind_direction > 337.5 and wind_direction <= 360):
                    wind_direction_str = 'North'
                elif wind_direction > 22.5 and wind_direction <= 67.5:
                    wind_direction_str = 'Northeast'
                elif wind_direction > 67.5 and wind_direction <= 112.5:
                    wind_direction_str = 'East'
                elif wind_direction > 112.5 and wind_direction <= 157.5:
                    wind_direction_str = 'Southeast'
                elif wind_direction > 157.5 and wind_direction <= 202.5:
                    wind_direction_str = 'South'
                elif wind_direction > 202.5 and wind_direction <= 247.5:
                    wind_direction_str = 'Southwest'
                elif wind_direction > 247.5 and wind_direction <= 292.5:
                    wind_direction_str = 'West'
                else:
                    wind_direction_str = 'Northwest'
            else:
                wind_direction_str = 'N/A'
            embed.add_field(name="Wind direction", value=wind_direction_str)
            embed.add_field(name="Wind gusts", value=f"{current.get('wind_gusts_10m', 'N/A')} mph")
            
            visibility = minutely_15.get('visibility', [0])
            if isinstance(visibility, list) and visibility:
                visibility_value = visibility[0] / 5280
            else:
                visibility_value = 0
            embed.add_field(name="Visibility", value=f"{visibility_value:.2f} miles")
            
            lightning_potential = minutely_15.get('lightning_potential', 'None')
            if isinstance(lightning_potential, list) and lightning_potential:
                lightning_potential = lightning_potential[0]
            if lightning_potential == 'None' or lightning_potential is None or lightning_potential == 0:
                lightning_potential_str = 'None'
            elif lightning_potential < 500:
                lightning_potential_str = 'Low'
            elif lightning_potential < 1000:
                lightning_potential_str = 'Medium'
            elif lightning_potential < 2000:
                lightning_potential_str = 'High'
            else:
                lightning_potential_str = 'Extreme'
            embed.add_field(name="Lightning potential", value=f"{lightning_potential_str}")
            embed.set_footer(text="When thunder roars, go indoors. If you can hear thunder, you can be struck by lightning.")
            
            # Fetch severe and extreme weather alerts
            alerts_url = f"https://api.weather.gov/alerts/active?point={latitude.strip()},{longitude.strip()}"
            async with self.session.get(alerts_url) as alerts_response:
                try:
                    alerts_response.raise_for_status()
                    alerts_data = await alerts_response.json()
                    alerts = alerts_data.get('features', [])
                    if alerts:
                        alert_titles = []
                        event_emojis = {
                            "Tornado Warning": ":cloud_tornado:",
                            "Severe Thunderstorm Warning": ":thunder_cloud_rain:",
                            "Flood Warning": ":ocean:",
                            "Heat Advisory": ":desert:",
                            "Special Weather Statement": ":information_source:",
                            "Winter Storm Warning": ":cloud_snow:",
                            "High Wind Warning": ":wind_blowing_face:",
                            "Fire Weather Watch": ":fire:",
                            "Flood Advisory": ":ocean:",
                            "Hurricane Warning": ":cyclone:",
                            "Tsunami Warning": ":ocean:",
                            "Earthquake Warning": ":earth_americas:",
                            "Blizzard Warning": ":snowflake:",
                            "Dust Storm Warning": ":dash:",
                            "Extreme Cold Warning": ":cold_face:",
                            "Extreme Heat Warning": ":hot_face:",
                            "Gale Warning": ":wind_face:",
                            "Ice Storm Warning": ":ice_cube:",
                            "Red Flag Warning": ":triangular_flag_on_post:",
                            "Severe Weather Statement": ":cloud_with_lightning_and_rain:",
                            "Special Marine Warning": ":anchor:",
                            "Storm Surge Warning": ":ocean:",
                            "Tropical Storm Warning": ":tropical_storm:",
                            "Volcano Warning": ":volcano:",
                            # Add more event types and corresponding emojis as needed
                        }
                        for alert in alerts:
                            event = alert['properties']['event']
                            emoji = event_emojis.get(event, ":warning:")  # Default to warning emoji if event not found
                            expires = alert['properties'].get('expires')
                            if expires:
                                try:
                                    expires_timestamp = f"<t:{int(datetime.fromisoformat(expires[:-1]).timestamp())}:R>"
                                except ValueError:
                                    # Attempt to correct the timestamp format
                                    try:
                                        corrected_expires = expires + '0'  # Adding missing zero
                                        expires_timestamp = f"<t:{int(datetime.fromisoformat(corrected_expires[:-1]).timestamp())}:R>"
                                    except ValueError as ve:
                                        expires_timestamp = f"Invalid expiry time format: {expires}"
                                alert_titles.append(f"{emoji} **{event}** ending **{expires_timestamp}**")
                            else:
                                alert_titles.append(f"{emoji} **{event}**")
                        alert_status = "\n".join(alert_titles)
                    else:
                        alert_status = "None right now **#ItsAmazingOutThere**"
                except Exception as e:
                    alert_status = f"Failed to fetch alerts: {str(e)}, url={alerts_url}"
            
            embed.add_field(name="Active alerts", value=alert_status, inline=False)
            
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
                
                for period in periods[:10]:  # Create a page for each of the next 5 forecast periods
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
                embed = discord.Embed(title=word, description=description, color=0xfffffe)
                pages.append(embed)

            if not pages:
                await ctx.send("No valid glossary terms found.")
                return

            message = await ctx.send(embed=pages[0])
            glossary_definitions_shown = await self.config.glossary_definitions_shown()
            await self.config.glossary_definitions_shown.set(glossary_definitions_shown + 1)
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
                        glossary_definitions_shown = await self.config.glossary_definitions_shown()
                        await self.config.glossary_definitions_shown.set(glossary_definitions_shown + 1)
                elif str(reaction) == "➡️":
                    if i < len(pages) - 1:
                        i += 1
                        await message.edit(embed=pages[i])
                        glossary_definitions_shown = await self.config.glossary_definitions_shown()
                        await self.config.glossary_definitions_shown.set(glossary_definitions_shown + 1)
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
        """Explore US weather observation stations"""
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
        """Explore US weather radar installations"""
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
                level_two_last_received_time = discord.utils.format_dt(discord.utils.parse_time(latency['levelTwoLastReceivedTime']), style='R')
                max_latency_time = discord.utils.format_dt(discord.utils.parse_time(latency['maxLatencyTime']), style='R')
                host = latency['host']
                
            description = f"Located at `{coordinates[1]}, {coordinates[0]}`, `{elevation} meters high` and operating in the `{time_zone}` timezone"

            embed = discord.Embed(title=f"{station_name} radar", description=description, color=0xfffffe)
            
            if rda_details is not None:
                rda_timestamp = rda_details.get("timestamp", "Unknown")
                if rda_timestamp != "Unknown":
                    rda_timestamp = discord.utils.format_dt(discord.utils.parse_time(rda_timestamp), style='R')
                if rda_timestamp != "Unknown":
                    embed.add_field(name="RDA time", value=rda_timestamp, inline=True)
                reporting_host = rda_details.get('reportingHost', 'Unknown').upper()
                if reporting_host != "UNKNOWN":
                    embed.add_field(name="Reporting host", value=f"`{reporting_host}`", inline=True)
                properties = rda_details.get("properties", {})
                resolution_version = properties.get('resolutionVersion', 'Unknown')
                if resolution_version != "Unknown":
                    embed.add_field(name="Resolution version", value=f"`{resolution_version}`", inline=True)
                nl2_path = properties.get('nl2Path', 'Unknown')
                if nl2_path != "Unknown":
                    embed.add_field(name="NL2 path", value=f"`{nl2_path}`", inline=True)
                volume_coverage_pattern = properties.get('volumeCoveragePattern', 'Unknown')
                if volume_coverage_pattern != "Unknown":
                    embed.add_field(name="Volume coverage pattern", value=f"`{volume_coverage_pattern}`", inline=True)
                control_status = properties.get('controlStatus', 'Unknown')
                if control_status != "Unknown":
                    embed.add_field(name="Control status", value=f"`{control_status}`", inline=True)
                build_number = properties.get('buildNumber', 'Unknown')
                if build_number != "Unknown":
                    embed.add_field(name="Build number", value=f"`{build_number}`", inline=True)
                alarm_summary = properties.get('alarmSummary', 'Unknown')
                if alarm_summary != "Unknown":
                    embed.add_field(name="Alarm summary", value=f"`{alarm_summary}`", inline=True)
                mode = properties.get('mode', 'Unknown')
                if mode != "Unknown":
                    embed.add_field(name="Mode", value=f"`{mode}`", inline=True)
                generator_state = properties.get('generatorState', 'Unknown')
                if generator_state != "Unknown":
                    embed.add_field(name="Generator state", value=f"`{generator_state}`", inline=True)
                super_resolution_status = properties.get('superResolutionStatus', 'Unknown')
                if super_resolution_status != "Unknown":
                    embed.add_field(name="Super resolution status", value=f"`{super_resolution_status}`", inline=True)
                operability_status = properties.get('operabilityStatus', 'Unknown')
                if operability_status != "Unknown":
                    embed.add_field(name="Operability status", value=f"`{operability_status}`", inline=True)
                status = properties.get('status', 'Unknown')
                if status != "Unknown":
                    embed.add_field(name="Status", value=f"`{status}`", inline=True)
                avg_transmitter_power = properties.get("averageTransmitterPower", {})
                avg_transmitter_power_value = avg_transmitter_power.get('value', 'Unknown')
                if avg_transmitter_power_value != "Unknown":
                    unit_code = avg_transmitter_power.get('unitCode', '').replace('wmoUnit:', '')
                    embed.add_field(name="Average transmitter power", value=f"`{avg_transmitter_power_value} {unit_code}`", inline=True)
                reflectivity_calibration = properties.get("reflectivityCalibrationCorrection", {})
                reflectivity_calibration_value = reflectivity_calibration.get('value', 'Unknown')
                if reflectivity_calibration_value != "Unknown":
                    unit_code = reflectivity_calibration.get('unitCode', '').replace('wmoUnit:', '')
                    embed.add_field(name="Reflectivity calibration correction", value=f"`{reflectivity_calibration_value} {unit_code}`", inline=True)
            
            if latency != "Unknown":
                if current_value is not None:
                    embed.add_field(name="Current latency", value=f"`{int(current_value)} ms`", inline=True)
                if average_value is not None:
                    embed.add_field(name="Average latency", value=f"`{int(average_value)} ms`", inline=True)
                if max_value is not None:
                    embed.add_field(name="Max latency", value=f"`{int(max_value)} ms`", inline=True)
                embed.add_field(name="L2 last received time", value=level_two_last_received_time, inline=True)
                embed.add_field(name="Max latency time", value=max_latency_time, inline=True)
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
                reaction, user = await self.bot.wait_for("reaction_add", timeout=90.0, check=check)
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

    @commands.group()
    async def weatherset(self, ctx):
        """Configure settings and features of weather"""

    @weatherset.command(name="profile")
    async def profile(self, ctx):
        """View your weather profile"""
        user = ctx.author
        user_data = await self.config.user(user).all()
        zip_code = user_data.get("zip_code", "Not set")
        severe_alerts_enabled = user_data.get("severealerts", False)
        freeze_alerts_enabled = user_data.get("freezealerts", False)
        heat_alerts_enabled = user_data.get("heatalerts", False)
        
        # Determine the current weather season
        month = datetime.now().month
        if month in [12, 1, 2]:
            season = "❄️ Winter"
        elif month in [3, 4, 5]:
            season = "🌸 Spring"
        elif month in [6, 7, 8]:
            season = "☀️ Summer"
        else:
            season = "🍂 Fall"
        
        embed = discord.Embed(
            title=f"Weather profile for {user.name}",
            color=0xfffffe
        )
        
        # Censor zip code if command is used in a public channel
        if isinstance(ctx.channel, discord.DMChannel):
            embed.add_field(name="Zip code", value=zip_code, inline=True)
        else:
            embed.add_field(name="Zip code", value="||Hidden||", inline=True)
        
        embed.add_field(name="Severe storm alerts", value="Enabled" if severe_alerts_enabled else "Disabled", inline=True)
        embed.add_field(name="Extreme cold alerts", value="Enabled" if freeze_alerts_enabled else "Disabled", inline=True)
        embed.add_field(name="Extreme heat alerts", value="Enabled" if heat_alerts_enabled else "Disabled", inline=True)
        embed.add_field(name="Local season", value=season, inline=True)
        
        await ctx.send(embed=embed)

    @commands.cooldown(1, 900, commands.BucketType.user)
    @weatherset.command(name="severealerts")
    async def severealerts(self, ctx):
        """Toggle severe alerts for your saved location"""
        user = ctx.author
        current_setting = await self.config.user(user).severealerts()
        new_setting = not current_setting

        if new_setting:
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
                await self.config.user(user).severealerts.set(True)
                await ctx.send("Weather alerts have been enabled.")
            except discord.Forbidden:
                await ctx.send("I cannot send you direct messages. Please enable DMs from server members and try again.")
        else:
            await self.config.user(user).severealerts.set(False)
            await ctx.send("Weather alerts have been disabled.")

    async def check_weather_alerts(self):
        """Check for weather alerts and DM users if any severe or extreme warnings are issued"""
        all_users = await self.config.all_users()
        users_with_alerts = [user_id for user_id, data in all_users.items() if data.get("severealerts")]

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

    async def start_severe_alerts_task(self):
        while True:
            await self.check_weather_alerts()
            await asyncio.sleep(900)

    @commands.cooldown(1, 900, commands.BucketType.user)
    @weatherset.command(name="freezealerts")
    async def freezealerts(self, ctx):
        """Toggle freeze alerts for your saved location"""
        user_data = await self.config.user(ctx.author).all()
        freeze_alerts_enabled = user_data.get("freezealerts", False)
        await self.config.user(ctx.author).freezealerts.set(not freeze_alerts_enabled)
        status = "enabled" if not freeze_alerts_enabled else "disabled"
        await ctx.send(f"Freeze alerts have been {status} for your location.")

    async def check_freeze_alerts(self):
        """Check for upcoming dangerously cold temperatures and DM users if any are expected"""
        all_users = await self.config.all_users()
        users_with_freeze_alerts = [user_id for user_id, data in all_users.items() if data.get("freezealerts")]

        for user_id in users_with_freeze_alerts:
            user_data = await self.config.user_from_id(user_id).all()
            zip_code = user_data.get("zip_code")
            if not zip_code or zip_code not in self.zip_codes:
                continue

            latitude, longitude = self.zip_codes[zip_code]
            forecast_url = f"https://api.weather.gov/points/{latitude.strip()},{longitude.strip()}/forecast"

            async with self.session.get(forecast_url) as response:
                if response.status != 200:
                    continue

                data = await response.json()
                periods = data.get('properties', {}).get('periods', [])
                cold_alerts = [period for period in periods if period['temperature'] <= 10]

                if cold_alerts:
                    user = self.bot.get_user(user_id)
                    if user:
                        for alert in cold_alerts:
                            embed = discord.Embed(
                                title="Extreme cold alert",
                                description=f"Expected dangerously cold temperatures: {alert['temperature']}°F",
                                color=0x1E90FF
                            )
                            embed.add_field(name="Time", value=alert['name'], inline=True)
                            embed.add_field(name="Detailed Forecast", value=alert['detailedForecast'], inline=False)
                            embed.set_footer(text="Stay warm and take necessary precautions.")

                            await user.send(embed=embed)
                            total_freeze_alerts_sent = await self.config.total_freeze_alerts_sent()
                            await self.config.total_freeze_alerts_sent.set(total_freeze_alerts_sent + 1)

    async def start_freeze_alerts_task(self):
        while True:
            await self.check_freeze_alerts()
            await asyncio.sleep(604800)  # 7 days in seconds

    @commands.cooldown(1, 900, commands.BucketType.user)
    @weatherset.command(name="heatalerts")
    async def heatalerts(self, ctx):
        """Toggle heat alerts for your saved location"""
        user_data = await self.config.user(ctx.author).all()
        heat_alerts_enabled = user_data.get("heatalerts", False)
        await self.config.user(ctx.author).heatalerts.set(not heat_alerts_enabled)
        status = "enabled" if not heat_alerts_enabled else "disabled"
        await ctx.send(f"Heat alerts have been {status} for your location.")

    async def check_heat_alerts(self):
        """Check for upcoming dangerously hot temperatures and DM users if any are expected"""
        all_users = await self.config.all_users()
        users_with_heat_alerts = [user_id for user_id, data in all_users.items() if data.get("heatalerts")]

        for user_id in users_with_heat_alerts:
            user_data = await self.config.user_from_id(user_id).all()
            zip_code = user_data.get("zip_code")
            if not zip_code or zip_code not in self.zip_codes:
                continue

            latitude, longitude = self.zip_codes[zip_code]
            forecast_url = f"https://api.weather.gov/points/{latitude.strip()},{longitude.strip()}/forecast"

            async with self.session.get(forecast_url) as response:
                if response.status != 200:
                    continue

                data = await response.json()
                periods = data.get('properties', {}).get('periods', [])
                heat_alerts = [period for period in periods if period['temperature'] >= 100]

                if heat_alerts:
                    user = self.bot.get_user(user_id)
                    if user:
                        for alert in heat_alerts:
                            embed = discord.Embed(
                                title="Extreme heat alert",
                                description=f"Expected dangerously hot temperatures: {alert['temperature']}°F",
                                color=0xFF4500
                            )
                            embed.add_field(name="Time", value=alert['name'], inline=True)
                            embed.add_field(name="Detailed Forecast", value=alert['detailedForecast'], inline=False)
                            embed.set_footer(text="Stay cool and take necessary precautions.")

                            await user.send(embed=embed)
                            total_heat_alerts_sent = await self.config.total_heat_alerts_sent()
                            await self.config.total_heat_alerts_sent.set(total_heat_alerts_sent + 1)

    async def start_heat_alerts_task(self):
        while True:
            await self.check_heat_alerts()
            await asyncio.sleep(604800)  # 7 days in seconds

    @weatherset.command(name="zip")
    async def zip(self, ctx, zip_code: str):
        """Set your zip code for queries"""
        # Validate the zip code against zipcodes.csv
        if zip_code not in self.zip_codes:
            await ctx.send("Invalid zip code. Please provide a valid zip code.")
            return

        await self.config.user(ctx.author).zip_code.set(zip_code)
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send(f"Your zip code has been set to `{zip_code}`. This is the location that will now be used in the future for your weather queries.")
        else:
            await ctx.send("Your zip code has been set. This is the location that will now be used in the future for your weather queries. For privacy reasons, the zip code is not displayed here. Use the `weatherset profile` command in a DM to see your saved settings.")
            await ctx.message.delete()

    
