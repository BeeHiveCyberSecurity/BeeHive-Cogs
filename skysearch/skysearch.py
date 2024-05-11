import discord #type: ignore
from discord.ext import tasks, commands
from redbot.core import commands, Config #type: ignore
import json
import aiohttp #type: ignore
import re
import asyncio
import typing
import os
import tempfile
import csv
import datetime
from reportlab.lib.pagesizes import letter, landscape, A4 #type: ignore
from reportlab.pdfgen import canvas #type: ignore 
from reportlab.lib import colors#type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle #type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle #type: ignore

class Skysearch(commands.Cog):
    law_enforcement_icao_set = {'A10941', 'AB68C8', 'A9A449', 'A67117', 'A03325', 'A1B4BB', 'A2C934', 'AD933E', 'AC6E92', 'A64D15', 'A6A665', 'A97B90', 'A7C42B', 'A92BFF'}  # Update this set as needed or discovered
    military_icao_set = {'AE055F', 'AE0270', 'AE1462', 'AE146E', 'AE0664'}
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.api_url = "https://api.airplanes.live/v2"
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color(0xfffffe)
        self.check_emergency_squawks.start()
        
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
            emergency_squawk_codes = ['7500', '7600', '7700']
            hex_id = aircraft_data.get('hex', '')                                      
            image_url, photographer = await self._get_photo_by_hex(hex_id)
            link = f"https://globe.airplanes.live/?icao={hex_id}"
            squawk_code = aircraft_data.get('squawk', 'N/A')
            if squawk_code == '7500':
                embed = discord.Embed(title='Aircraft information', color=discord.Colour(0xFF9145))
                emergency_status = ":warning: **Aircraft has been hijacked**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            elif squawk_code == '7600':
                embed = discord.Embed(title='Aircraft information', color=discord.Colour(0xFF9145))
                emergency_status = ":warning: **Aircraft has lost radio contact**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            elif squawk_code == '7700':
                embed = discord.Embed(title='Aircraft information', color=discord.Colour(0xFF9145))
                emergency_status = ":warning: **Aircraft has declared an emergency**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            else:
                embed = discord.Embed(title='Aircraft information', color=discord.Colour(0xfffffe))
                emergency_status = ":shield: **Flight is safe and secure**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            embed.set_image(url=image_url)
            embed.set_footer(text="")
            embed.add_field(name="Type", value=f"**{aircraft_data.get('desc', 'N/A')} ({aircraft_data.get('t', 'N/A')})**", inline=False)
            callsign = aircraft_data.get('flight', 'N/A').strip()
            if not callsign or callsign == 'N/A':
                callsign = 'HIDDEN'
            embed.add_field(name="Callsign", value=f"**{callsign}**", inline=True)
            embed.add_field(name="Registration", value=f"**{aircraft_data.get('reg', 'UNKNOWN')}**", inline=True)
            embed.add_field(name="ICAO", value=f"**{aircraft_data.get('hex', 'N/A').upper()}**", inline=True)
            altitude = aircraft_data.get('alt_baro', 'N/A')
            ground_speed = aircraft_data.get('gs', 'N/A')
            if altitude == 'ground':
                embed.add_field(name="Status", value="`On ground`", inline=True)
            else:
                altitude_feet = f"{altitude} ft"
                embed.add_field(name="Altitude", value=f"`{altitude_feet}`", inline=True)
            heading = aircraft_data.get('true_heading', None)
            if heading is not None:
                if 0 <= heading < 45:
                    emoji = ":arrow_upper_right:"
                elif 45 <= heading < 90:
                    emoji = ":arrow_right:"
                elif 90 <= heading < 135:
                    emoji = ":arrow_lower_right:"
                elif 135 <= heading < 180:
                    emoji = ":arrow_down:"
                elif 180 <= heading < 225:
                    emoji = ":arrow_lower_left:"
                elif 225 <= heading < 270:
                    emoji = ":arrow_left:"
                elif 270 <= heading < 315:
                    emoji = ":arrow_upper_left:"
                else:
                    emoji = ":arrow_up:"
                embed.add_field(name="Heading", value=f"{emoji} `{heading}°`", inline=True)
            lat = aircraft_data.get('lat', 'N/A')
            lon = aircraft_data.get('lon', 'N/A')
            if lat != 'N/A':
                lat = round(float(lat), 2)
                lat_dir = "N" if lat >= 0 else "S"
                lat = f"{abs(lat)}{lat_dir}"
            if lon != 'N/A':
                lon = round(float(lon), 2)
                lon_dir = "E" if lon >= 0 else "W"
                lon = f"{abs(lon)}{lon_dir}"
            if lat != 'N/A' and lon != 'N/A':
                embed.add_field(name="Position", value=f"`{lat}, {lon}`", inline=True)
            embed.add_field(name="Squawk", value=f"`{aircraft_data.get('squawk', 'SILENT')}`", inline=True)
            if aircraft_data.get('year', None) is not None:
                embed.add_field(name="Built", value=f"`{aircraft_data.get('year')}`", inline=True)
            category = aircraft_data.get('category', None)
            if category is not None:
                embed.add_field(name="Category", value=f"`{category}`", inline=True)
            embed.add_field(name="Aircraft model", value=f"`{aircraft_data.get('t', 'UNKNOWN')}`", inline=True)
            ground_speed_knots = aircraft_data.get('gs', 'N/A')
            if ground_speed_knots != 'N/A':
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)  # Convert knots to mph
                embed.add_field(name="Speed", value=f"`{ground_speed_mph} mph`", inline=True)
            else:
                embed.add_field(name="Speed", value="UNKNOWN", inline=True)
            operator = aircraft_data.get('ownOp', None)
            if operator is not None:
                embed.add_field(name="Operated by", value=f"`{operator}`", inline=True)
            baro_rate = aircraft_data.get('baro_rate', 'N/A')
            if baro_rate == 'N/A':
                embed.add_field(name="Altitude trend", value=":grey_question: Altitude trends unavailable, not enough data...", inline=False)
            else:
                baro_rate_fps = round(int(baro_rate) / 60, 2)  # Convert feet per minute to feet per second
                if abs(baro_rate_fps) < 50/60:
                    embed.add_field(name="Altitude trend", value=":arrow_right: **Maintaining altitude @ **  " + f"**`{baro_rate_fps} feet/sec`**", inline=False)
                elif baro_rate_fps > 0:
                    embed.add_field(name="Altitude trend", value=":arrow_upper_right: **Climbing @**  " + f"**`{baro_rate_fps} feet/sec`**", inline=False)
                else:
                    embed.add_field(name="Altitude trend", value=":arrow_lower_right: **Descending @ ** " + f"**`{abs(baro_rate_fps)} feet/sec`**", inline=False)
            embed.add_field(name="Safety status", value=emergency_status, inline=True)


            icao = aircraft_data.get('hex', None)
            if icao and icao.upper() in self.law_enforcement_icao_set:
                embed.add_field(name="Historical usage", value=":police_officer: **This aircraft is known to be used for law enforcement purposes, such as traffic enforcement, or search and rescue missions**", inline=False)
            if icao and icao.upper() in self.military_icao_set:
                embed.add_field(name="Historical usage", value=":military_helmet: **This aircraft is known to be used for military or combat purposes**", inline=False)

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label=f"Track live", url=f"{link}", style=discord.ButtonStyle.link))
            await ctx.send(embed=embed, view=view)
            squawk_code = aircraft_data.get('squawk', 'N/A')
            if squawk_code in emergency_squawk_codes:
                emergency_embed = discord.Embed(title='This aircraft is declaring an air emergency', color=discord.Colour(0xFF9145))
                if squawk_code == '7500':
                    emergency_embed.add_field(name="Squawk 7500 - Hijacking", value="The pilots of this aircraft have indicated that the plane is being hijacked. Check local news if this is a domestic flight, or the news channels of the airport the flight is scheduled to arrive at.", inline=False)
                elif squawk_code == '7600':
                    emergency_embed.add_field(name="Squawk 7600 - Radio failure", value="This code is used to indicate a radio failure. While this code is squawked, assume an aircraft is in a location where reception and/or communication, and thus tracking, may be poor, restricted, or non-existant.", inline=False)
                elif squawk_code == '7700':
                    emergency_embed.add_field(name="Squawk 7700 - General emergency", value="This code is used to indicate a general emergency. The pilot currently has ATC priority and is working to resolve the situation. Check local news outlets for more information, or if this is a military flight, look into what squadron the plane belonged to, and if they posted any updates later in the day.", inline=False)
                await ctx.send(embed=emergency_embed)
        else:
            embed = discord.Embed(title='No results found for your query', color=discord.Colour(0xff4545))
            embed.add_field(name="Details", value="No aircraft information found or the response format is incorrect.", inline=False)
            message = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await ctx.message.delete()
            await message.delete()

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

    @commands.group(name='skysearch', help='Get information about aircraft.', invoke_without_command=True)
    async def aircraft_group(self, ctx):
        """Summon the SkySearch panel"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="SkySearch is ready",
                description="### You can use this to search the skies for information about planes, including their locations, callsigns, emergency status, and more. Select below what you'd like to use SkySearch to do.",
                color=discord.Color.from_str("#fffffe")
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            view = discord.ui.View(timeout=180)  # Set a timeout for the view

            # Create buttons with click actions
            search_callsign = discord.ui.Button(label=f"Search by callsign", style=discord.ButtonStyle.green, row=1)
            search_icao = discord.ui.Button(label="Search by ICAO", style=discord.ButtonStyle.green, row=1)
            search_registration = discord.ui.Button(label="Search by registration", style=discord.ButtonStyle.green, row=1)
            search_squawk = discord.ui.Button(label="Search by squawk", style=discord.ButtonStyle.green, row=1)
            search_type = discord.ui.Button(label="Search by model", style=discord.ButtonStyle.green, row=1)
            search_radius = discord.ui.Button(label="Search within radius", style=discord.ButtonStyle.green, row=2)
            show_military = discord.ui.Button(label="Show military aircraft", style=discord.ButtonStyle.danger, row=3)
            show_ladd = discord.ui.Button(label="Show LADD-restricted aircraft", style=discord.ButtonStyle.danger, row=3)
            show_pia = discord.ui.Button(label="Show aircraft using private ICAO's", style=discord.ButtonStyle.danger, row=3)
            show_the_commands = discord.ui.Button(label="Show available commands", style=discord.ButtonStyle.grey, row=4)
            show_stats = discord.ui.Button(label="Show stats", style=discord.ButtonStyle.grey, row=4)

            # Define button callbacks
            async def search_callsign_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This SkySearch panel doesn't belong to you. Start your own using `[p]skysearch`", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="### Please reply with the `callsign` you want to search the skies for.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_callsign(ctx, message.content)

            async def show_military_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This SkySearch panel doesn't belong to you. Start your own using `[p]skysearch`", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="### Fetching data for military aircraft...",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                await ctx.send(embed=embed)
                
                await self.show_military_aircraft(ctx)

            async def search_icao_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This SkySearch panel doesn't belong to you. Start your own using `[p]skysearch`", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="### Please reply with the `ICAO` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_icao(ctx, message.content)

            async def search_registration_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="### Please reply with the `registration` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_reg(ctx, message.content)

            async def search_squawk_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="### Please reply with the `squawk code` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_squawk(ctx, message.content)

            async def search_type_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="### Please reply with the `model` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_type(ctx, message.content)

            async def show_the_commands_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                await ctx.send_help(self.aircraft_group)

            async def search_radius_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()

                # Prompt for latitude
                embed = discord.Embed(
                    title="",
                    description="### Please reply with the latitude.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                latitude = message.content

                # Prompt for longitude
                embed.description = "### Please reply with the longitude."
                await ctx.send(embed=embed)
                message = await self.bot.wait_for('message', check=check)
                longitude = message.content

                # Prompt for radius
                embed.description = "### Please reply with the radius in miles you want to search within."
                await ctx.send(embed=embed)
                message = await self.bot.wait_for('message', check=check)
                radius = message.content

                await self.aircraft_within_radius(ctx, latitude, longitude, radius)

            async def show_stats_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                await self.stats(ctx)

            async def show_ladd_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                await self.ladd_aircraft(ctx)

            async def show_pia_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button", ephemeral=True)
                    return
                await interaction.response.defer()
                await self.pia_aircraft(ctx)

            # Assign callbacks to buttons
            search_callsign.callback = search_callsign_callback
            search_icao.callback = search_icao_callback
            search_registration.callback = search_registration_callback
            search_squawk.callback = search_squawk_callback
            search_type.callback = search_type_callback
            search_radius.callback = search_radius_callback
            show_military.callback = show_military_callback
            show_the_commands.callback = show_the_commands_callback
            show_stats.callback = show_stats_callback
            show_ladd.callback = show_ladd_callback
            show_pia.callback = show_pia_callback

            # Add buttons to the view
            view.add_item(search_callsign)
            view.add_item(search_icao)
            view.add_item(search_registration)
            view.add_item(search_squawk)
            view.add_item(search_type)
            view.add_item(search_radius)
            view.add_item(show_military)
            view.add_item(show_ladd)
            view.add_item(show_pia)
            view.add_item(show_the_commands)
            view.add_item(show_stats)

            # Send the embed with the view
            await ctx.send(embed=embed, view=view)

    @aircraft_group.command(name='icao', help='Get information about an aircraft by its 24-bit ICAO Address')
    async def aircraft_by_icao(self, ctx, hex_id: str):
        url = f"{self.api_url}/hex/{hex_id}"
        response = await self._make_request(url)
        if response:
            if 'ac' in response and len(response['ac']) > 1:
                for aircraft_info in response['ac']:
                    await self._send_aircraft_info(ctx, {'ac': [aircraft_info]})
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)
    @aircraft_group.command(name='callsign', help='Get information about an aircraft by its callsign.')
    async def aircraft_by_callsign(self, ctx, callsign: str):
        url = f"{self.api_url}/callsign/{callsign}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="No aircraft found with the specified callsign.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='reg', help='Get information about an aircraft by its registration.')
    async def aircraft_by_reg(self, ctx, registration: str):
        url = f"{self.api_url}/reg/{registration}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='type', help='Get information about aircraft by its type.')
    async def aircraft_by_type(self, ctx, aircraft_type: str):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='squawk', help='Get information about an aircraft by its squawk code.')
    async def aircraft_by_squawk(self, ctx, squawk_value: str):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='military', help='Get information about military aircraft.')
    async def show_military_aircraft(self, ctx):
        url = f"{self.api_url}/mil"
        response = await self._make_request(url)
        if response:
            if len(response['ac']) > 1:
                pages = [response['ac'][i:i + 10] for i in range(0, len(response['ac']), 10)]  # Split aircraft list into pages of 10
                for page_index, page in enumerate(pages):
                    embed = discord.Embed(title=f"Military Aircraft (Page {page_index + 1}/{len(pages)})", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    for aircraft in page:
                        aircraft_description = aircraft.get('desc', 'N/A')  # Aircraft Description
                        aircraft_squawk = aircraft.get('squawk', 'N/A')  # Squawk
                        aircraft_lat = aircraft.get('lat', 'N/A')  # Latitude
                        aircraft_lon = aircraft.get('lon', 'N/A')  # Longitude
                        aircraft_heading = aircraft.get('heading', 'N/A')  # Heading
                        aircraft_speed = aircraft.get('spd', 'N/A')  # Speed
                        aircraft_hex = aircraft.get('hex', 'N/A')  # Hex

                        aircraft_info = f"**Squawk:** {aircraft_squawk}\n"
                        aircraft_info += f"**Coordinates:** Lat: {aircraft_lat}, Lon: {aircraft_lon}\n"
                        aircraft_info += f"**Heading:** {aircraft_heading}\n"
                        aircraft_info += f"**Speed:** {aircraft_speed}\n"
                        aircraft_info += f"**Hex:** {aircraft_hex}"

                        embed.add_field(name=aircraft_description, value=aircraft_info, inline=False)

                    message = await ctx.send(embed=embed)
                    await message.add_reaction("⬅️")  # Adding a reaction to scroll to the previous page
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next page

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        if str(reaction.emoji) == '⬅️' and page_index > 0:  # Check if the previous page reaction was added and it's not the first page
                            await message.delete()
                            page_index -= 1
                        elif str(reaction.emoji) == '➡️' and page_index < len(pages) - 1:  # Check if the next page reaction was added and it's not the last page
                            await message.delete()
                            page_index += 1
                    except asyncio.TimeoutError:
                        await message.delete()
                        break
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='ladd', help='Get information on LADD-restricted aircraft')
    async def ladd_aircraft(self, ctx):
        url = f"{self.api_url}/ladd"
        response = await self._make_request(url)
        if response:
            if len(response['ac']) > 1:
                pages = [response['ac'][i:i + 10] for i in range(0, len(response['ac']), 10)]  # Split aircraft list into pages of 10
                for page_index, page in enumerate(pages):
                    embed = discord.Embed(title=f"Limited Aircraft Data Displayed (Page {page_index + 1}/{len(pages)})", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    for aircraft in page:
                        aircraft_description = aircraft.get('desc', 'N/A')  # Aircraft Description
                        aircraft_squawk = aircraft.get('squawk', 'N/A')  # Squawk
                        aircraft_lat = aircraft.get('lat', 'N/A')  # Latitude
                        aircraft_lon = aircraft.get('lon', 'N/A')  # Longitude
                        aircraft_heading = aircraft.get('heading', 'N/A')  # Heading
                        aircraft_speed = aircraft.get('spd', 'N/A')  # Speed
                        aircraft_hex = aircraft.get('hex', 'N/A')  # Hex

                        aircraft_info = f"**Squawk:** {aircraft_squawk}\n"
                        aircraft_info += f"**Coordinates:** Lat: {aircraft_lat}, Lon: {aircraft_lon}\n"
                        aircraft_info += f"**Heading:** {aircraft_heading}\n"
                        aircraft_info += f"**Speed:** {aircraft_speed}\n"
                        aircraft_info += f"**Hex:** {aircraft_hex}"

                        embed.add_field(name=aircraft_description, value=aircraft_info, inline=False)

                    message = await ctx.send(embed=embed)
                    await message.add_reaction("⬅️")  # Adding a reaction to scroll to the previous page
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next page

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        if str(reaction.emoji) == '⬅️' and page_index > 0:  # Check if the previous page reaction was added and it's not the first page
                            await message.delete()
                            page_index -= 1
                        elif str(reaction.emoji) == '➡️' and page_index < len(pages) - 1:  # Check if the next page reaction was added and it's not the last page
                            await message.delete()
                            page_index += 1
                    except asyncio.TimeoutError:
                        await message.delete()
                        break
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='pia', help='View live aircraft using private ICAO addresses')
    async def pia_aircraft(self, ctx):
        url = f"{self.api_url}/pia"
        response = await self._make_request(url)
        if response:
            if len(response['ac']) > 1:
                pages = [response['ac'][i:i + 10] for i in range(0, len(response['ac']), 10)]  # Split aircraft list into pages of 10
                for page_index, page in enumerate(pages):
                    embed = discord.Embed(title=f"Private ICAO Aircraft Data Displayed (Page {page_index + 1}/{len(pages)})", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    for aircraft in page:
                        aircraft_description = aircraft.get('desc', 'N/A')  # Aircraft Description
                        aircraft_squawk = aircraft.get('squawk', 'N/A')  # Squawk
                        aircraft_lat = aircraft.get('lat', 'N/A')  # Latitude
                        aircraft_lon = aircraft.get('lon', 'N/A')  # Longitude
                        aircraft_heading = aircraft.get('heading', 'N/A')  # Heading
                        aircraft_speed = aircraft.get('spd', 'N/A')  # Speed
                        aircraft_hex = aircraft.get('hex', 'N/A')  # Hex

                        aircraft_info = f"**Squawk:** {aircraft_squawk}\n"
                        aircraft_info += f"**Coordinates:** Lat: {aircraft_lat}, Lon: {aircraft_lon}\n"
                        aircraft_info += f"**Heading:** {aircraft_heading}\n"
                        aircraft_info += f"**Speed:** {aircraft_speed}\n"
                        aircraft_info += f"**Hex:** {aircraft_hex}"

                        embed.add_field(name=aircraft_description, value=aircraft_info, inline=False)

                    message = await ctx.send(embed=embed)
                    await message.add_reaction("⬅️")  # Adding a reaction to scroll to the previous page
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next page

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        if str(reaction.emoji) == '⬅️' and page_index > 0:  # Check if the previous page reaction was added and it's not the first page
                            await message.delete()
                            page_index -= 1
                        elif str(reaction.emoji) == '➡️' and page_index < len(pages) - 1:  # Check if the next page reaction was added and it's not the last page
                            await message.delete()
                            page_index += 1
                    except asyncio.TimeoutError:
                        await message.delete()
                        break
            else:
                await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='radius', help='Get information about aircraft within a specified radius.')
    async def aircraft_within_radius(self, ctx, lat: str, lon: str, radius: str):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information for aircraft within the specified radius.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='export', help='Search aircraft by ICAO, callsign, squawk, or type and export the results.')
    async def export_aircraft(self, ctx, search_type: str, search_value: str, file_format: str):
        if search_type not in ["icao", "callsign", "squawk", "type"]:
            embed = discord.Embed(title="Error", description="Invalid search type specified. Use one of: icao, callsign, squawk, or type.", color=0xfa4545)
            await ctx.send(embed=embed)
            return

        if search_type == "icao":
            search_type = "hex"

        url = f"{self.api_url}/{search_type}/{search_value}"
        response = await self._make_request(url)
        if response:
            if file_format not in ["csv", "pdf", "txt", "html"]:
                embed = discord.Embed(title="Error", description="Invalid file format specified. Use one of: csv, pdf, txt, or html.", color=0xfa4545)
                await ctx.send(embed=embed)
                return

            if not response['ac']:
                embed = discord.Embed(title="Error", description="No aircraft data found.", color=0xfa4545)
                await ctx.send(embed=embed)
                return

            file_name = f"{search_type}_{search_value}.{file_format.lower()}"
            file_path = os.path.join(tempfile.gettempdir(), file_name)

            try:
                if file_format.lower() == "csv":
                    with open(file_path, "w", newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        aircraft_keys = list(response['ac'][0].keys())
                        writer.writerow([key.upper() for key in aircraft_keys])
                        for aircraft in response['ac']:
                            aircraft_values = list(map(str, aircraft.values()))
                            writer.writerow(aircraft_values)
                elif file_format.lower() == "pdf":
                    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4)) 
                    styles = getSampleStyleSheet()
                    styles.add(ParagraphStyle(name='Normal-Bold', fontName='Helvetica-Bold', fontSize=14, leading=16, alignment=1)) 
                    flowables = []

                    flowables.append(Paragraph(f"<u>{search_type.capitalize()} {search_value}</u>", styles['Normal-Bold'])) 
                    flowables.append(Spacer(1, 24)) 

                    aircraft_keys = list(response['ac'][0].keys())
                    data = [Paragraph(f"<b>{key}</b>", styles['Normal-Bold']) for key in aircraft_keys]
                    flowables.extend(data)

                    for aircraft in response['ac']:
                        aircraft_values = list(map(str, aircraft.values()))
                        data = [Paragraph(value, styles['Normal']) for value in aircraft_values]
                        flowables.extend(data)
                        flowables.append(PageBreak())

                    doc.build(flowables)
                elif file_format.lower() in ["txt"]:
                    with open(file_path, "w", newline='', encoding='utf-8') as file:
                        aircraft_keys = list(response['ac'][0].keys())
                        file.write(' '.join([key.upper() for key in aircraft_keys]) + '\n')
                        for aircraft in response['ac']:
                            aircraft_values = list(map(str, aircraft.values()))
                            file.write(' '.join(aircraft_values) + '\n')
                elif file_format.lower() == "html":
                    with open(file_path, "w", newline='', encoding='utf-8') as file:
                        aircraft_keys = list(response['ac'][0].keys())
                        file.write('<table>\n')
                        file.write('<tr>\n')
                        for key in aircraft_keys:
                            file.write(f'<th>{key.upper()}</th>\n')
                        file.write('</tr>\n')
                        for aircraft in response['ac']:
                            aircraft_values = list(map(str, aircraft.values()))
                            file.write('<tr>\n')
                            for value in aircraft_values:
                                file.write(f'<td>{value}</td>\n')
                            file.write('</tr>\n')
                        file.write('</table>\n')
            except PermissionError as e:
                embed = discord.Embed(title="Error", description="I do not have permission to write to the file system.", color=0xff4545)
                await ctx.send(embed=embed)
                if os.path.exists(file_path):
                    os.remove(file_path)

            with open(file_path, 'rb') as fp:
                await ctx.send(file=discord.File(fp, filename=os.path.basename(file_path)))
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='stats', help='Get statistics about SkySearch and the data used here')
    async def stats(self, ctx):
        url = "https://api.airplanes.live/stats"

        try:
            if not hasattr(self, '_http_client'):
                self._http_client = aiohttp.ClientSession()
            async with self._http_client.get(url) as response:
                data = await response.json()

            if all(key in data for key in ["beast", "mlat", "other", "aircraft"]):
                stats_keys = ["beast", "mlat", "other", "aircraft"]
                stats_values = {key: data[key] for key in stats_keys}

                embed = discord.Embed(title="Data from Airplanes.Live", description="Select data is brought to you free-of-charge by [airplanes.live](https://airplanes.live)", color=0xfffffe)
                embed.set_image(url="https://asset.brandfetch.io/id1hdkKy3B/idqsgDGEm_.png")
                embed.set_thumbnail(url="https://asset.brandfetch.io/id1hdkKy3B/idgRk5S59l.jpeg")
                for key, value in stats_values.items():
                    embed.add_field(name=key.capitalize(), value="{:,} planes".format(value), inline=True)
                embed2 = discord.Embed(title="Enhanced by BeeHive Intelligence", description="BeeHive tracks and supplements this cog's original dataset during day-to-day operations.", color=0xffd966)
                embed2.set_image(url="https://asset.brandfetch.io/idGpYEfxfH/id0xj4J1xg.png")
                embed2.set_thumbnail(url="https://asset.brandfetch.io/idGpYEfxfH/idW3166yGx.png")
                embed2.add_field(name="Law enforcement aircraft catalogued", value="{:,} planes".format(len(self.law_enforcement_icao_set)), inline=False)
                embed2.add_field(name="Military aircraft catalogued", value="{:,} planes".format(len(self.military_icao_set)), inline=False)
                embed3 = discord.Embed(title="Photography courtesy of PlaneSpotters.net", description="Some aircraft have photos available taken by skilled independent photographers - this is where they come from.", color=0xfffffe)

                await ctx.send(embed=embed)
                await ctx.send(embed=embed3)
                await ctx.send(embed=embed2)
            else:
                embed = discord.Embed(title="Error", description="Incomplete data received from API.", color=0xff4545)
                await ctx.send(embed=embed)
        except aiohttp.ClientError as e:
            embed = discord.Embed(title="Error", description=f"Error fetching data: {e}", color=0xff4545)
            await ctx.send(embed=embed)

    @aircraft_group.command(name='scroll', help='Scroll through available planes.')
    async def scroll_planes(self, ctx):
        url = f"{self.api_url}/mil"
        try:
            response = await self._make_request(url)
            if response and 'ac' in response:
                for index, aircraft_info in enumerate(response['ac']):
                    await self._send_aircraft_info(ctx, {'ac': [aircraft_info]})
                    embed = discord.Embed(description=f"Plane {index + 1}/{len(response['ac'])}. React with ➡️ to view the next plane or ⏹️ to stop.")
                    message = await ctx.send(embed=embed)
                    await message.add_reaction("➡️")  # Adding a reaction to scroll to the next plane
                    await message.add_reaction("⏹️")  # Adding a reaction to stop scrolling

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == '➡️' or str(reaction.emoji) == '⏹️'  # Updated to check for stop reaction as well

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction.emoji, ctx.author)  # Remove the reaction after processing
                        if str(reaction.emoji) == '⏹️':  # Check if the stop reaction was added
                            embed = discord.Embed(description="Stopping.")
                            await ctx.send(embed=embed)
                            break
                    except asyncio.TimeoutError:
                        embed = discord.Embed(description="No reaction received. Stopping.")
                        await ctx.send(embed=embed)
                        break
        except Exception as e:
            embed = discord.Embed(description=f"An error occurred during scrolling: {e}.")
            await ctx.send(embed=embed)

    @aircraft_group.command(name='showalertchannel', help='Show alert task status and output if set')
    async def list_alert_channels(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Squawk alerts for {guild.name}", color=0xfffffe)
        alert_channel_id = await self.config.guild(guild).alert_channel()
        if alert_channel_id:
            alert_channel = self.bot.get_channel(alert_channel_id)
            if alert_channel:
                next_iteration = self.check_emergency_squawks.next_iteration
                now = datetime.datetime.now(datetime.timezone.utc)  # Ensure datetime is timezone aware
                if next_iteration:
                    time_remaining = (next_iteration - now).total_seconds()
                    if time_remaining > 0:  # Ensure time remaining is not negative
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                else:
                    time_remaining = self.check_emergency_squawks.seconds
                    if time_remaining > 0:  # Ensure time remaining is not negative
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                if self.check_emergency_squawks.is_running():
                    last_check_status = f":white_check_mark: **Checked successfully, next checking {time_remaining_formatted}**"
                else:
                    last_check_status = f":x: **Last check failed, retrying {time_remaining_formatted}**"
                embed.add_field(name="Status", value=f"Channel: {alert_channel.mention}\nLast check: {last_check_status}", inline=False)
                
                # Add field for the last time an aircraft squawked an emergency
                last_emergency_squawk_time = await self.config.guild(guild).last_emergency_squawk_time()
                if last_emergency_squawk_time:
                    last_emergency_squawk_time_formatted = f"<t:{int(last_emergency_squawk_time)}:F>"
                    embed.add_field(name="Last Emergency Squawk", value=f"Time: {last_emergency_squawk_time_formatted}", inline=False)
                else:
                    embed.add_field(name="Last Emergency Squawk", value="No emergency squawks yet.", inline=False)
            else:
                embed.add_field(name="Status", value="No alert channel set.", inline=False)
        else:
            embed.add_field(name="Status", value="No alert channel set.", inline=False)
        await ctx.send(embed=embed)
        
    @aircraft_group.command(name='alertchannel', help='Set a channel to send emergency squawk alerts to.')
    async def set_alert_channel(self, ctx, channel: discord.TextChannel):
        try:
            await self.config.guild(ctx.guild).alert_channel.set(channel.id)
            await ctx.send(f"Alert channel set to {channel.mention}")
        except Exception as e:
            await ctx.send(f"Error setting alert channel: {e}")

    @tasks.loop(minutes=2)
    async def check_emergency_squawks(self):
        try:
            emergency_squawk_codes = ['7500', '7600', '7700']
            for squawk_code in emergency_squawk_codes:
                url = f"{self.api_url}/squawk/{squawk_code}"
                response = await self._make_request(url)
                if response and 'ac' in response:
                    for aircraft_info in response['ac']:
                        guilds = self.bot.guilds
                        for guild in guilds:
                            alert_channel_id = await self.config.guild(guild).alert_channel()
                            if alert_channel_id:
                                alert_channel = self.bot.get_channel(alert_channel_id)
                                if alert_channel:
                                    # Check if the alert has already been sent
                                    previous_alerts = await alert_channel.history(limit=100).flatten()
                                    for message in previous_alerts:
                                        if aircraft_info['icao'] in message.content:
                                            # If the alert has been sent, delete the old message
                                            await message.delete()
                                            break
                                    # Send the new alert
                                    await self._send_aircraft_info(alert_channel, {'ac': [aircraft_info]})
                await asyncio.sleep(2)  # Add a delay to respect API rate limit
        except Exception as e:
            print(f"Error checking emergency squawks: {e}")

    @check_emergency_squawks.before_loop
    async def before_check_emergency_squawks(self):
        try:
            await self.bot.wait_until_ready()
        except Exception as e:
            print(f"Error before checking emergency squawks: {e}")

    def cog_unload(self):
        try:
            self.check_emergency_squawks.cancel()
        except Exception as e:
            print(f"Error unloading cog: {e}")
