import discord
from redbot.core import commands, Config
import json
import aiohttp
import re
import asyncio

class Airplaneslive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.api_url = "https://api.airplanes.live/v2"
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color.blue() 

    async def cog_unload(self):
        if hasattr(self, '_http_client'):
            await self._http_client.close()

    async def _make_request(self, url):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error making request: {e}")
            return None

    async def _send_aircraft_info(self, ctx, response):
        if 'ac' in response and response['ac']:                                            
            aircraft_data = response['ac'][0]
            hex_id = aircraft_data.get('hex', '')                                      
            image_url, photographer = await self._get_photo_by_hex(hex_id)
            link = f"https://globe.airplanes.live/?icao={hex_id}"
            embed = discord.Embed(title='Aircraft Information', color=self.EMBED_COLOR)
            embed.set_image(url=image_url)
            embed.set_footer(text="Powered by Planespotters.net and airplanes.live ✈️")
            embed.add_field(name="Flight", value=aircraft_data.get('flight', 'N/A').strip(), inline=True)
            embed.add_field(name="Type", value=f"{aircraft_data.get('desc', 'N/A')} ({aircraft_data.get('t', 'N/A')})", inline=True)
            embed.add_field(name="Altitude", value=f"{aircraft_data.get('alt_baro', 'N/A')} feet", inline=True)
            embed.add_field(name="Ground Speed", value=f"{aircraft_data.get('gs', 'N/A')} knots", inline=True)
            embed.add_field(name="Heading", value=f"{aircraft_data.get('true_heading', 'N/A')} degrees", inline=True)
            embed.add_field(name="Position", value=f"{aircraft_data.get('lat', 'N/A')}, {aircraft_data.get('lon', 'N/A')}", inline=True)
            embed.add_field(name="Squawk", value=aircraft_data.get('squawk', 'N/A'), inline=True)
            embed.add_field(name="Emergency", value=aircraft_data.get('emergency', 'N/A'), inline=True)
            embed.add_field(name="Operator", value=aircraft_data.get('ownOp', 'N/A'), inline=True)
            embed.add_field(name="Year", value=aircraft_data.get('year', 'N/A'), inline=True)
            embed.add_field(name="Category", value=aircraft_data.get('category', 'N/A'), inline=True)
            embed.add_field(name="Aircraft Type", value=aircraft_data.get('t', 'N/A'), inline=True)
            embed.add_field(name="Speed", value=f"{aircraft_data.get('gs', 'N/A')} knots", inline=True)
            embed.add_field(name="Altitude Rate", value=f"{aircraft_data.get('baro_rate', 'N/A')} feet/minute", inline=True)
            embed.add_field(name="Vertical Rate", value=f"{aircraft_data.get('geom_rate', 'N/A')} feet/minute", inline=True)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Track flight live", url=f"{link}", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send("No aircraft information found or the response format is incorrect.\n\nThe plane may be not currently in use or the data is not available at the moment")

    async def _get_photo_by_hex(self, hex_id):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(f'https://api.planespotters.net/pub/photos/hex/{hex_id}') as response:
                if response.status == 200:
                    json_out = await response.json()
                    if 'photos' in json_out and json_out['photos']:
                        photo = json_out['photos'][0]
                        url = photo.get('thumbnail_large', {}).get('src', '')
                        photographer = photo.get('photographer', '')
                        return url, photographer
        except (KeyError, IndexError, aiohttp.ClientError):
            pass
        return None, None

    @commands.hybrid_group(name='aircraft', help='Get information about aircraft.')
    async def aircraft_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid aircraft command passed.')

    @aircraft_group.command(name='hex', help='Get information about an aircraft by its hexadecimal identifier.')
    async def aircraft_by_hex(self, ctx, hex_id: str):
        url = f"{self.api_url}/hex/{hex_id}"
        response = await self._make_request(url)
        if response:
            if 'ac' in response and len(response['ac']) > 1:
                for aircraft_info in response['ac']:
                    await self._send_aircraft_info(ctx, {'ac': [aircraft_info]})
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='callsign', help='Get information about an aircraft by its callsign.')
    async def aircraft_by_callsign(self, ctx, callsign: str):
        url = f"{self.api_url}/callsign/{callsign}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("No aircraft found with the specified callsign.")

    @aircraft_group.command(name='reg', help='Get information about an aircraft by its registration.')
    async def aircraft_by_reg(self, ctx, registration: str):
        url = f"{self.api_url}/reg/{registration}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='type', help='Get information about aircraft by its type.')
    async def aircraft_by_type(self, ctx, aircraft_type: str):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='squawk', help='Get information about an aircraft by its squawk code.')
    async def aircraft_by_squawk(self, ctx, squawk_value: str):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information.")

    @aircraft_group.command(name='military', help='Get information about military aircraft.')
    async def military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving military aircraft information.")

    @aircraft_group.command(name='ladd', help='Limiting Aircraft Data Displayed (LADD).')
    async def ladd_aircraft(self, ctx):
        url = f"{self.api_url}/ladd"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving LADD aircraft information.")

    @aircraft_group.command(name='pia', help='Privacy ICAO Address.')
    async def pia_aircraft(self, ctx):
        url = f"{self.api_url}/pia"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving PIA aircraft information.")

    @aircraft_group.command(name='radius', help='Get information about aircraft within a specified radius.')
    async def aircraft_within_radius(self, ctx, lat: str, lon: str, radius: str):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            await ctx.send("Error retrieving aircraft information within the specified radius.")

    @aircraft_group.command(
        name='json', 
        help='Retrieve aircraft information in various formats based on identifier type.'
    )
    async def json(self, ctx, identifier: str, identifier_type: str = None):
        # Determine the type of aircraft identifier provided if not specified
        if identifier_type is None:
            if re.match(r'^[0-9a-fA-F]{6}$', identifier):
                identifier_type = "hex"
            elif re.match(r'^[0-9]{4}$', identifier):
                identifier_type = "squawk"
            elif re.match(r'^[A-Z0-9]{2,7}$', identifier, re.I):
                identifier_type = "callsign"
            else:
                identifier_type = "type"  # Default to type if no match found and type not specified
        
        if identifier_type not in ["hex", "squawk", "callsign", "type"]:
            await ctx.send("Invalid identifier type specified. Use one of: hex, squawk, callsign, or type.")
            return
        
        url = f"{self.api_url}/{identifier_type}/{identifier}"
        
        try:
            response = await self._make_request(url)
            if not response:
                raise ValueError("Failed to receive data from the API.")
            
            aircraft_info = self._format_response(response)
            json_data = json.dumps(aircraft_info, indent=4)
            await ctx.send(f"```json\n{json_data}\n```")
        except Exception as e:
            await ctx.send(f"Failed to retrieve aircraft information: {e}")


    @aircraft_group.command(name='stats', help='Get https://airplanes.live feeder stats.')
    async def stats(self, ctx):
        url = "https://api.airplanes.live/stats"

        try:
            if not hasattr(self, '_http_client'):
                self._http_client = aiohttp.ClientSession()
            async with self._http_client.get(url) as response:
                data = await response.json()

            if "beast" in data and "mlat" in data and "other" in data and "aircraft" in data:
                beast_stats = data["beast"]
                mlat_stats = data["mlat"]
                other_stats = data["other"]
                aircraft_stats = data["aircraft"]

                embed = discord.Embed(title="airplanes.live Stats", color=0x00ff00)
                embed.set_thumbnail(url="https://airplanes.live/img/airplanes-live-logo.png")
                embed.add_field(name="Beast", value=beast_stats, inline=False)
                embed.add_field(name="MLAT", value=mlat_stats, inline=False)
                embed.add_field(name="Other", value=other_stats, inline=False)
                embed.add_field(name="Aircraft", value=aircraft_stats, inline=False)

                await ctx.send(embed=embed)
            else:
                await ctx.send("Incomplete data received from API.")
        except aiohttp.ClientError as e:
            await ctx.send(f"Error fetching data: {e}")

    @aircraft_group.command(name='alert', help='Set up configurable alerts for specific keywords.')
    async def alert(self, ctx, keyword: str, identifier_type: str, channel: discord.TextChannel, force_update: bool = False):
        try:
            if not hasattr(self, 'alerts'):
                self.alerts = {}

            if identifier_type not in ["hex", "squawk", "callsign", "type"]:
                await ctx.send("Invalid identifier type specified. Use one of: hex, squawk, callsign, or type.")
                return

            if keyword in self.alerts and self.alerts[keyword][1] == channel:
                if not force_update:
                    await ctx.send(f"Alert for keyword '{keyword}' already exists in channel '{channel.name}'.")
                    return

            self.alerts[keyword] = (identifier_type, channel)
            await ctx.send(f"Alert set up for keyword '{keyword}' with identifier type '{identifier_type}' in channel '{channel.name}'.")
        except Exception as e:
            await ctx.send(f"An error occurred while setting up the alert: {e}")
    
    @aircraft_group.command(name='force_update', help='Force an update for a specific alert.')
    async def force_update(self, ctx, keyword: str, identifier_type: str, channel: discord.TextChannel):
        try:
            if not hasattr(self, 'alerts'):
                await ctx.send("No alerts configured.")
                return
            
            if (keyword, (identifier_type, channel)) not in self.alerts.items():
                await ctx.send(f"No alert found for keyword '{keyword}' with identifier type '{identifier_type}' in channel '{channel.name}'.")
                return
            
            self.alerts[keyword] = (identifier_type, channel)
            await ctx.send(f"Forced update for alert with keyword '{keyword}' and identifier type '{identifier_type}' in channel '{channel.name}'.")
        except Exception as e:
            await ctx.send(f"An error occurred while forcing an update for the alert: {e}")

    @aircraft_group.command(name='check_alerts', help='Check all configured alerts.')
    async def check_alerts(self, ctx):
        try:
            if not hasattr(self, 'alerts') or not self.alerts:
                await ctx.send("No alerts configured.")
                return
            
            alerts_list = "\n".join([f"Keyword: {keyword}, Channel: {channel.name}, Identifier Type: {identifier_type}" for keyword, (identifier_type, channel) in self.alerts.items()])
            await ctx.send(f"Configured Alerts:\n{alerts_list}")
        except Exception as e:
            await ctx.send(f"An error occurred while checking alerts: {e}")

    async def _scroll_through_planes(self, ctx, response):
        if 'ac' in response:
            for aircraft_info in response['ac']:
                await self._send_aircraft_info(ctx, {'ac': [aircraft_info]})
        else:
            await ctx.send("No aircraft information found or the response format is incorrect. The plane may not be currently in use or the data is not available at the moment.")


            

    @aircraft_group.command(name='scroll', help='Scroll through available planes.')
    async def scroll_planes(self, ctx):
        url = f"{self.api_url}/mil"
        try:
            response = await self._make_request(url)
            if response and 'ac' in response:
                for index, aircraft_info in enumerate(response['ac']):
                    await self._send_aircraft_info(ctx, {'ac': [aircraft_info]})
                    message = await ctx.send(f"Plane {index + 1}/{len(response['ac'])}. React with ➡️ to view the next plane or ⏹️ to stop.")
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next plane
                    await message.add_reaction("⏹️")  # Adding a reaction to stop scrolling

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == '➡️' or str(reaction.emoji) == '⏹️'  # Updated to check for stop reaction as well

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction.emoji, ctx.author)  # Remove the reaction after processing
                        if str(reaction.emoji) == '⏹️':  # Check if the stop reaction was added
                            await ctx.send("Stopping.")
                            break
                    except asyncio.TimeoutError:
                        await ctx.send("No reaction received. Stopping.")
                        break
        except Exception as e:
            await ctx.send(f"An error occurred during scrolling: {e}.")

            @tasks.loop(minutes=15)
            async def send_alerts(self):
                for keyword, (identifier_type, channel) in self.alerts.items():
                    try:
                        url = f"{self.api_url}/{keyword}"
                        response = await self._make_request(url)
                        if response and 'ac' in response:
                            for aircraft_info in response['ac']:
                                if identifier_type in aircraft_info:
                                    await channel.send(f"Alert for {keyword}: {aircraft_info[identifier_type]}")
                    except Exception as e:
                        print(f"An error occurred while sending alerts: {e}")
