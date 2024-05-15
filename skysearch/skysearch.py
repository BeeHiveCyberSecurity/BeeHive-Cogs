import discord #type: ignore
import json
import aiohttp #type: ignore
import re
import asyncio
import urllib
import typing
import os
import io
import tempfile
import csv
import datetime
import time
import requests
from discord.ext import tasks, commands #type: ignore
from redbot.core import commands, Config #type: ignore
from reportlab.lib.pagesizes import letter, landscape, A4 #type: ignore
from reportlab.pdfgen import canvas #type: ignore 
from reportlab.lib import colors#type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle #type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle #type: ignore
from .icao_codes import law_enforcement_icao_set, military_icao_set, medical_icao_set, suspicious_icao_set, newsagency_icao_set, balloons_icao_set, global_prior_known_accident_set, ukr_conflict_set, agri_utility_set

class Skysearch(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        self.api_url = "https://api.airplanes.live/v2"
        self.max_requests_per_user = 10
        self.EMBED_COLOR = discord.Color(0xfffffe)
        self.check_emergency_squawks.start()
        self.law_enforcement_icao_set = law_enforcement_icao_set
        self.military_icao_set = military_icao_set
        self.medical_icao_set = medical_icao_set
        self.suspicious_icao_set = suspicious_icao_set
        self.newsagency_icao_set = newsagency_icao_set
        self.balloons_icao_set = balloons_icao_set
        self.global_prior_known_accident_set = global_prior_known_accident_set
        self.ukr_conflict_set = ukr_conflict_set
        self.agri_utility_set = agri_utility_set
        
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
            await ctx.typing()
            aircraft_data = response['ac'][0]
            emergency_squawk_codes = ['7500', '7600', '7700']
            hex_id = aircraft_data.get('hex', '')                                      
            image_url, photographer = await self._get_photo_by_hex(hex_id)
            link = f"https://globe.airplanes.live/?icao={hex_id}"
            squawk_code = aircraft_data.get('squawk', 'N/A')
#            if squawk_code == '7400':
#                embed = discord.Embed(title='Aircraft information', color=discord.Colour(0xff9145))
#                emergency_status = ":warning: **UAV has lost radio contact**"
#                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            if squawk_code == '7500':
                embed = discord.Embed(title='Aircraft found', description=f"# {aircraft_data.get('desc', 'N/A')}", color=discord.Colour(0xFF9145))
                emergency_status = ":rotating_light: **Aircraft has been hijacked**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            elif squawk_code == '7600':
                embed = discord.Embed(title='Aircraft found', description=f"# {aircraft_data.get('desc', 'N/A')}", color=discord.Colour(0xFF9145))
                emergency_status = ":signal_strength: **Aircraft has lost radio contact**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            elif squawk_code == '7700':
                embed = discord.Embed(title='Aircraft found', description=f"# {aircraft_data.get('desc', 'N/A')}", color=discord.Colour(0xFF9145))
                emergency_status = ":large_orange_diamond: **Aircraft has declared an emergency**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
            else:
                embed = discord.Embed(title='Aircraft found', description=f"# {aircraft_data.get('desc', 'N/A')}", color=discord.Colour(0xfffffe))
                emergency_status = ":ballot_box_with_check: **Aircraft reports normal conditions**"
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            callsign = aircraft_data.get('flight', 'N/A').strip()
            if not callsign or callsign == 'N/A':
                callsign = 'BLOCKED'
            embed.add_field(name="Callsign", value=f"**`{callsign}`**", inline=True)
            registration = aircraft_data.get('reg', None)
            if registration is not None:
                registration = registration.upper()
                embed.add_field(name="Registration", value=f"**`{registration}`**", inline=True)
            icao = aircraft_data.get('hex', 'N/A').upper()
            embed.add_field(name="ICAO", value=f"**`{icao}`**", inline=True)
            altitude = aircraft_data.get('alt_baro', 'N/A')
            ground_speed = aircraft_data.get('gs', 'N/A')
            if altitude == 'ground':
                embed.add_field(name="Status", value="**`On ground`**", inline=True)
            elif altitude != 'N/A':
                if isinstance(altitude, int):
                    altitude = "{:,}".format(altitude)
                altitude_feet = f"{altitude} ft"
                embed.add_field(name="Altitude", value=f"**`{altitude_feet}`**", inline=True)
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
                embed.add_field(name="Heading", value=f"{emoji} **`{heading}°`**", inline=True)
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
                embed.add_field(name="Position", value=f"**`{lat}, {lon}`**", inline=True)
            embed.add_field(name="Squawk", value=f"**`{aircraft_data.get('squawk', 'BLOCKED')}`**", inline=True)
            if aircraft_data.get('year', None) is not None:
                embed.add_field(name="Built", value=f"**`{aircraft_data.get('year')}`**", inline=True)
            
            aircraft_model = aircraft_data.get('t', None)
            if aircraft_model is not None:
                embed.add_field(name="Model", value=f"**`{aircraft_model}`**", inline=True)
            ground_speed_knots = aircraft_data.get('gs', 'N/A')
            if ground_speed_knots != 'N/A':
                ground_speed_mph = round(float(ground_speed_knots) * 1.15078)  # Convert knots to mph
                embed.add_field(name="Speed", value=f"**`{ground_speed_mph} mph`**", inline=True)
            category_code_to_label = {
                "A0": "`No info available`",
                "A1": "`Light (< 15500 lbs)`",
                "A2": "`Small (15500 to 75000 lbs)`",
                "A3": "`Large (75000 to 300000 lbs)`",
                "A4": "`High vortex large`",
                "A5": "`Heavy (> 300000 lbs)`",
                "A6": "`High performance (> 5g acceleration and 400 kts)`",
                "A7": "`Rotorcraft`",
                "B0": "`No info available`",
                "B1": "`Glider / sailplane`",
                "B2": "`Lighter-than-air`",
                "B3": "`Parachutist / skydiver`",
                "B4": "`Ultralight / hang-glider / paraglider`",
                "B5": "`Reserved`",
                "B6": "`UAV`",
                "B7": "`Space / trans-atmospheric vehicle`",
                "C0": "`No info available`",
                "C1": "`Emergency vehicle`",
                "C2": "`Service vehicle`",
                "C3": "`Point obstacle`",
                "C4": "`Cluster obstacle`",
                "C5": "`Line obstacle`",
                "C6": "`Reserved`",
                "C7": "`Reserved`"
            }
            category = aircraft_data.get('category', None)
            if category is not None:
                category_label = category_code_to_label.get(category, "Unknown category")
                embed.add_field(name="Category", value=f"**{category_label}**", inline=False)

            operator = aircraft_data.get('ownOp', None)
            if operator is not None:
                embed.add_field(name="Operated by", value=f"**`{operator}`**", inline=True)
            
            seen_pos = aircraft_data.get('seen_pos', 'N/A')
            current_timestamp = int(time.time())
            if seen_pos != 'N/A':
                seen_pos_timestamp = current_timestamp - int(seen_pos)
                last_checked_in_value = f"**<t:{seen_pos_timestamp}:R>**"
            else:
                last_checked_in_value = "**<t:{current_timestamp}:R>**"
            embed.add_field(name="Last checked in", value=last_checked_in_value, inline=False)
            
            baro_rate = aircraft_data.get('baro_rate', 'N/A')
            if baro_rate == 'N/A':
                embed.add_field(name="Altitude trend", value=":grey_question: **Altitude trends unavailable, not enough data...**", inline=False)
            else:
                baro_rate_fps = round(int(baro_rate) / 60, 2)  # Convert feet per minute to feet per second
                if abs(baro_rate_fps) < 50/60:
                    embed.add_field(name="Altitude data", value=":cloud: **Maintaining consistent altitude**", inline=False)
                elif baro_rate_fps > 0:
                    embed.add_field(name="Altitude data", value=":airplane_departure: **Climbing @**  " + f"**{baro_rate_fps} feet/sec**", inline=False)
                else:
                    embed.add_field(name="Altitude data", value=":airplane_arriving: **Descending @ ** " + f"**{abs(baro_rate_fps)} feet/sec**", inline=False)
            embed.add_field(name="Flight status", value=emergency_status, inline=True)


            icao = aircraft_data.get('hex', None).upper()
            if icao and icao.upper() in self.law_enforcement_icao_set:
                embed.add_field(name="Asset intelligence", value=":police_officer: **Known for use by state law enforcement**", inline=False)
            if icao and icao.upper() in self.military_icao_set:
                embed.add_field(name="Asset intelligence", value=":military_helmet: **Known for use in military and government**", inline=False)
            if icao and icao.upper() in self.medical_icao_set:
                embed.add_field(name="Asset intelligence", value=":hospital: **Known for use in medical response and transport**", inline=False)
            if icao and icao.upper() in self.suspicious_icao_set:
                embed.add_field(name="Asset intelligence", value=":warning: **Exhibits suspicious flight or surveillance activity**", inline=False)
            if icao and icao.upper() in self.global_prior_known_accident_set:
                embed.add_field(name="Asset intelligence", value=":boom: **Prior involved in one or more documented accidents**", inline=False)
            if icao and icao.upper() in self.ukr_conflict_set:
                embed.add_field(name="Asset intelligence", value=":flag_ua: **Utilized within the [Russo-Ukrainian conflict](https://en.wikipedia.org/wiki/Russian-occupied_territories_of_Ukraine)**", inline=False)
            if icao and icao.upper() in self.newsagency_icao_set:
                embed.add_field(name="Asset intelligence", value=":newspaper: **Used by news or media organization**", inline=False)
            if icao and icao.upper() in self.balloons_icao_set:
                embed.add_field(name="Asset intelligence", value=":balloon: **Aircraft is a balloon**", inline=False)
            if icao and icao.upper() in self.agri_utility_set:
                embed.add_field(name="Asset intelligence", value=":corn: **Used for agriculture surveys, easement validation, or land inspection**", inline=False)

            image_url, photographer = await self._get_photo_by_hex(icao)
            if image_url and photographer:
                embed.set_image(url=image_url)
                embed.set_footer(text=f"📸 {photographer}")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="View on map", emoji="🗺️", url=f"{link}", style=discord.ButtonStyle.link))
            ground_speed_mph = ground_speed_mph if 'ground_speed_mph' in locals() else 'unknown'
            squawk_code = aircraft_data.get('squawk', 'N/A')
            if squawk_code in emergency_squawk_codes:
                tweet_text = f"Spotted an aircraft declaring an emergency! #Squawk #{squawk_code}, flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. #SkySearch #Emergency\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
            else:
                tweet_text = f"Tracking flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph using #SkySearch\n\nJoin via Discord to search and discuss planes with your friends for free - https://discord.gg/X8huyaeXrA"
            tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote_plus(tweet_text)}"
            view.add_item(discord.ui.Button(label=f"Post on 𝕏", emoji="📣", url=tweet_url, style=discord.ButtonStyle.link))
            whatsapp_text = f"Check out this aircraft! Flight {aircraft_data.get('flight', '')} at position {lat}, {lon} with speed {ground_speed_mph} mph. Track live @ https://globe.airplanes.live/?icao={icao} #SkySearch"
            whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote_plus(whatsapp_text)}"
            view.add_item(discord.ui.Button(label="Send on WhatsApp", emoji="📱", url=whatsapp_url, style=discord.ButtonStyle.link))
            await ctx.send(embed=embed, view=view)

#           squawk_code = aircraft_data.get('squawk', 'N/A')
#            if squawk_code in emergency_squawk_codes:
#               emergency_embed = discord.Embed(title='Aircraft emergency', color=discord.Colour(0xFF9145))
#                if squawk_code == '7500':
#                   emergency_embed.add_field(name="Squawk 7500 - Hijacking", value="The pilots of this aircraft have indicated that the plane is being hijacked. Check local news if this is a domestic flight, or the news channels of the airport the flight is scheduled to arrive at.", inline=False)
#                elif squawk_code == '7600':
#                    emergency_embed.add_field(name="Squawk 7600 - Radio failure", value="This code is used to indicate a radio failure. While this code is squawked, assume an aircraft is in a location where reception and/or communication, and thus tracking, may be poor, restricted, or non-existant.", inline=False)
#                elif squawk_code == '7700':
#                    emergency_embed.add_field(name="Squawk 7700 - General emergency", value="This code is used to indicate a general emergency. The pilot currently has ATC priority and is working to resolve the situation. Check local news outlets for more information, or if this is a military flight, look into what squadron the plane belonged to, and if they posted any updates later in the day.", inline=False)
#                await ctx.send(embed=emergency_embed)

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

    @commands.guild_only()
    @commands.group(name='aircraft', help='Get information about aircraft.', invoke_without_command=True, aliases=["skysearch"])
    async def aircraft_group(self, ctx):
        """Summon the aircraft panel"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Search aircraft",
                description="**SkySearch is a powerful tool that allows you to search for real-time information about aircraft**\n\nYou can search **active** aircraft by `callsign`, `ICAO`, `registration`, `squawk`, and `model`.\n\nYou can also search within a specific `radius`, view military aircraft, view LADD-restricted aircraft, view aircraft using private ICAO addresses, and more...\n\n**Use a button below to get started**",
                color=discord.Color.from_str("#fffffe")
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            view = discord.ui.View(timeout=180)  # Set a timeout for the view

            # Create buttons with click actions
            search_callsign = discord.ui.Button(label=f"Search callsign", style=discord.ButtonStyle.green, row=1)
            search_icao = discord.ui.Button(label="Search ICAO", style=discord.ButtonStyle.green, row=1)
            search_registration = discord.ui.Button(label="Search registration", style=discord.ButtonStyle.green, row=1)
            search_squawk = discord.ui.Button(label="Search squawk", style=discord.ButtonStyle.green, row=1)
            search_type = discord.ui.Button(label="Search model", style=discord.ButtonStyle.green, row=1)
            search_radius = discord.ui.Button(label="Search radius", style=discord.ButtonStyle.green, row=2)
            show_military = discord.ui.Button(label="Show military", style=discord.ButtonStyle.danger, row=3)
            show_ladd = discord.ui.Button(label="Show limited", style=discord.ButtonStyle.danger, row=3)
            show_pia = discord.ui.Button(label="Show private", style=discord.ButtonStyle.danger, row=3)
            show_the_commands = discord.ui.Button(label="Show help", style=discord.ButtonStyle.grey, row=4)
            show_stats = discord.ui.Button(label="Show stats", style=discord.ButtonStyle.grey, row=4)

            # Define button callbacks
            async def search_callsign_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This SkySearch panel doesn't belong to you. Start your own using `[p]skysearch`", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="## Please reply with the `callsign` you want to search the skies for.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_callsign(ctx, message.content)

            async def show_military_callback(interaction):
                await ctx.typing()
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This SkySearch panel doesn't belong to you. Start your own using `[p]skysearch`", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="## Fetching data for military aircraft...",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                await ctx.send(embed=embed)
                
                await self.show_military_aircraft(ctx)

            async def search_icao_callback(interaction):
                await ctx.typing()
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This SkySearch panel doesn't belong to you. Start your own using `[p]skysearch`", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="## Please reply with the `aircraft ICAO` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.aircraft_by_icao(ctx, message.content)

            async def search_registration_callback(interaction):
                await ctx.typing()
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="## Please reply with the `aircraft registration` you want to search.",
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
                    description="## Please reply with the `squawk code` you want to search.",
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
                    description="## Please reply with the `aircraft model` you want to search.",
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
                    description="## Please reply with the latitude.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                latitude = message.content

                # Prompt for longitude
                embed.description = "## Please reply with the longitude."
                await ctx.send(embed=embed)
                message = await self.bot.wait_for('message', check=check)
                longitude = message.content

                # Prompt for radius
                embed.description = "## Please reply with the radius in miles you want to search within, up to 250 miles."
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

    @commands.guild_only()
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
    
    @commands.guild_only()
    @aircraft_group.command(name='callsign', help='Get information about an aircraft by its callsign.')
    async def aircraft_by_callsign(self, ctx, callsign: str):
        url = f"{self.api_url}/callsign/{callsign}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="No aircraft found with the specified callsign.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='reg', help='Get information about an aircraft by its registration.')
    async def aircraft_by_reg(self, ctx, registration: str):
        url = f"{self.api_url}/reg/{registration}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='type', help='Get information about aircraft by its type.')
    async def aircraft_by_type(self, ctx, aircraft_type: str):
        url = f"{self.api_url}/type/{aircraft_type}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @aircraft_group.command(name='squawk', help='Get information about an aircraft by its squawk code.')
    async def aircraft_by_squawk(self, ctx, squawk_value: str):
        url = f"{self.api_url}/squawk/{squawk_value}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
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
                        aircraft_info += f"**ICAO:** {aircraft_hex}"

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
    
    @commands.guild_only()
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
                        aircraft_info += f"**ICAO:** {aircraft_hex}"

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

    @commands.guild_only()
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
                        aircraft_info += f"**ICAO:** {aircraft_hex}"

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

    @commands.guild_only()
    @aircraft_group.command(name='radius', help='Get information about aircraft within a specified radius.')
    async def aircraft_within_radius(self, ctx, lat: str, lon: str, radius: str):
        url = f"{self.api_url}/point/{lat}/{lon}/{radius}"
        response = await self._make_request(url)
        if response:
            await self._send_aircraft_info(ctx, response)
        else:
            embed = discord.Embed(title="Error", description="Error retrieving aircraft information for aircraft within the specified radius.", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
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

    @commands.guild_only()
    @aircraft_group.command(name='stats', help='Get statistics about SkySearch and the data used here')
    async def stats(self, ctx):
        url = "https://api.airplanes.live/stats"

        try:
            if not hasattr(self, '_http_client'):
                self._http_client = aiohttp.ClientSession()
            async with self._http_client.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    raise aiohttp.ClientError(f"API responded with status code: {response.status}")

            stats_fields = {
                "beast": {"name": "Beast Mode", "value": "**`{} feeders`**"},
                "mlat": {"name": "MLAT", "value": "**`{} feeders`**"},
                "other": {"name": "Other", "value": "**`{} feeders`**"},
                "aircraft": {"name": "Total Aircraft", "value": "**`{} aircraft`**"}
            }

            embed = discord.Embed(title="Air traffic data", description="Live flight data powered by [airplanes.live](https://airplanes.live) API", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            for key, field in stats_fields.items():
                if key in data:
                    name = field["name"]
                    value = field["value"].format("{:,}".format(data[key]))
                    embed.add_field(name=name, value=value, inline=True)

            embed.add_field(name="Appears in", value="`aircraft callsign` `aircraft icao` `aircraft reg` `aircraft squawk` `aircraft type` `aircraft radius` `aircraft pia` `aircraft mil` `aircraft ladd`", inline=False)

            embed2 = discord.Embed(title="Enhanced by BeeHive Intelligence", description="Additional info available per-aircraft", color=0xffd966)
            embed2.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/sparkles.png")
            embed2.add_field(name="Law enforcement aircraft", value="**`{:,} tagged`**".format(len(self.law_enforcement_icao_set)), inline=True)
            embed2.add_field(name="Military & government aircraft", value="**`{:,} tagged`**".format(len(self.military_icao_set)), inline=True)
            embed2.add_field(name="Medical aircraft", value="**`{:,} tagged`**".format(len(self.medical_icao_set)), inline=True)
            embed2.add_field(name="Media aircraft", value="**`{:,} known`**".format(len(self.newsagency_icao_set)), inline=True)
            embed2.add_field(name="Damaged aircraft", value="**`{:,} known`**".format(len(self.global_prior_known_accident_set)), inline=True)
            embed2.add_field(name="Wartime aircraft", value="**`{:,} observed`**".format(len(self.ukr_conflict_set)), inline=True)
            embed2.add_field(name="Utility aircraft", value="**`{:,} spotted`**".format(len(self.agri_utility_set)), inline=True)
            embed2.add_field(name="Balloons", value="**`{:,} known`**".format(len(self.balloons_icao_set)), inline=True)
            embed2.add_field(name="Suspicious aircraft", value="**`{:,} identifiers`**".format(len(self.suspicious_icao_set)), inline=True)

            embed3 = discord.Embed(title="Photography", description="Photos are powered by community contributions at [planespotters.net](https://www.planespotters.net/)", color=0xfffffe)
            embed3.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/camera.png")
            embed3.add_field(name="Appears in", value="**`aircraft callsign` `aircraft icao` `aircraft reg` `aircraft squawk` `aircraft type`**", inline=False)

            embed4 = discord.Embed(title="Airport data", description="Airport data is powered by the [airport-data.com](https://www.airport-data.com/) API service", color=0xfffffe)
            embed4.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/location.png")
            embed4.add_field(name="Appears in", value="**`airport about`**", inline=False)

            embed5 = discord.Embed(title="Runway data", description="Runway data is powered by the [airportdb.io](https://airportdb.io) API service", color=0xfffffe)
            embed5.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/layers.png")
            embed5.add_field(name="Appears in", value="**`airport runway`**", inline=False)

            embed6 = discord.Embed(title="Mapping and imagery", description="Mapping and ground imagery powered by [Google Maps](https://maps.google.com) and the [Maps Static API](https://developers.google.com/maps/documentation/maps-static)", color=0xfffffe)
            embed6.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/logo-google.png")
            embed6.add_field(name="Appears in", value="**`airport about`**", inline=False)

            await ctx.send(embed=embed)
            await ctx.send(embed=embed2)
            await ctx.send(embed=embed3)
            await ctx.send(embed=embed4)
            await ctx.send(embed=embed5)
            await ctx.send(embed=embed6)
        except aiohttp.ClientError as e:
            embed = discord.Embed(title="Error", description=f"Error fetching data: {e}", color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
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
                    await message.add_reaction("➡️")
                    await message.add_reaction("⏹️") 

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == '➡️' or str(reaction.emoji) == '⏹️'

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction.emoji, ctx.author)
                        if str(reaction.emoji) == '⏹️':
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

    @commands.guild_only()
    @aircraft_group.command(name='showalertchannel', help='Show alert task status and output if set')
    async def list_alert_channels(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Squawk alerts for {guild.name}", color=0xfffffe)
        alert_channel_id = await self.config.guild(guild).alert_channel()
        if alert_channel_id:
            alert_channel = self.bot.get_channel(alert_channel_id)
            if alert_channel:
                next_iteration = self.check_emergency_squawks.next_iteration
                now = datetime.datetime.now(datetime.timezone.utc)
                if next_iteration:
                    time_remaining = (next_iteration - now).total_seconds()
                    if time_remaining > 0: 
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                else:
                    time_remaining = self.check_emergency_squawks.seconds
                    if time_remaining > 0:
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                if self.check_emergency_squawks.is_running():
                    last_check_status = f":white_check_mark: **Checked successfully, next checking {time_remaining_formatted}**"
                else:
                    last_check_status = f":x: **Last check failed, retrying {time_remaining_formatted}**"
                embed.add_field(name="Status", value=f"Channel: {alert_channel.mention}\nLast check: {last_check_status}", inline=False)
                
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

    @commands.guild_only()   
    @aircraft_group.command(name='alertchannel', help='Set or clear a channel to send emergency squawk alerts to. Clear with no channel.')
    async def set_alert_channel(self, ctx, channel: discord.TextChannel = None):
        if channel:
            try:
                await self.config.guild(ctx.guild).alert_channel.set(channel.id)
                embed = discord.Embed(description=f"Alert channel set to {channel.mention}", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.config.guild(ctx.guild).alert_channel.clear()
                embed = discord.Embed(description="Alert channel cleared. No more alerts will be sent.", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @aircraft_group.command(name='autoicao')
    async def autoicao(self, ctx, state: bool = None):
        """Enable or disable automatic ICAO lookup."""
        if state is None:
            state = await self.config.guild(ctx.guild).auto_icao()
            if state:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup is currently enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup is currently disabled.", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            await self.config.guild(ctx.guild).auto_icao.set(state)
            if state:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup has been enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup has been disabled.", color=0xff4545)
                await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.group(name='airport', help='Get information about airports.', invoke_without_command=True, aliases=["groundsearch"])
    async def airport_group(self, ctx):
         """Summon SkySearch ground search panel"""
         if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Airport search",
                description="**You can search for real time information about airports using SkySearch. Select what you'd like to search below.**",
                color=discord.Color.from_str("#fffffe")
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            view = discord.ui.View(timeout=180)  # Set a timeout for the view

            # Create buttons with click actions
            search_airport = discord.ui.Button(label="Airport info", style=discord.ButtonStyle.green, row=1)
            search_runway = discord.ui.Button(label="Runway info", style=discord.ButtonStyle.green, row=1)
            show_the_commands = discord.ui.Button(label="Show help", style=discord.ButtonStyle.grey, row=4)
            show_stats = discord.ui.Button(label="Show stats", style=discord.ButtonStyle.grey, row=4)

            async def search_airport_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="## Please reply with the `airport code` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.airportinfo(ctx, message.content)

            async def search_runway_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button", ephemeral=True)
                    return
                await interaction.response.defer()
                embed = discord.Embed(
                    title="",
                    description="## Please reply with the `airport code` you want to search.",
                    color=discord.Color.from_str("#fffffe")
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/search.png")
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author
                message = await self.bot.wait_for('message', check=check)
                await self.runwayinfo(ctx, message.content)

            async def show_stats_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                await self.stats(ctx)

            async def show_the_commands_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
                    return
                await interaction.response.defer()
                await ctx.send_help(self.airport_group)

            search_airport.callback = search_airport_callback
            show_the_commands.callback = show_the_commands_callback
            show_stats.callback = show_stats_callback
            search_runway.callback = search_runway_callback

            # Add buttons to the view

            view.add_item(search_airport)
            view.add_item(search_runway)
            view.add_item(show_the_commands)
            view.add_item(show_stats)

            # Send the embed with the view
            await ctx.send(embed=embed, view=view)

    @commands.guild_only()
    @airport_group.command(name='about')
    async def airportinfo(self, ctx, code: str = None):
        """Query airport information by ICAO or IATA code."""
        if code is None:
            embed = discord.Embed(title="Error", description="Please provide an ICAO or IATA code.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        # Determine if the code is ICAO or IATA based on length
        if len(code) == 4:
            code_type = 'icao'
        elif len(code) == 3:
            code_type = 'iata'
        else:
            embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        try:
            url1 = f"https://www.airport-data.com/api/ap_info.json?{code_type}={code}"
            embed = discord.Embed(title=f"Airport information for {code.upper()}", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/location.png")
            fields = {
                'icao': 'ICAO Code',
                'iata': 'IATA Code',
                'name': 'Name',
                'location': 'Location',
                'country': 'Country',
                'country_code': 'Country Code',
                'longitude': 'Longitude',
                'latitude': 'Latitude'
            }
            response1 = requests.get(url1)
            data1 = response1.json()

            googlemaps_tokens = await self.bot.get_shared_api_tokens("googlemaps")
            google_street_view_api_key = googlemaps_tokens.get("api_key", "YOUR_API_KEY")  # Use the API key from the shared tokens, default to "YOUR_API_KEY" if not found
            
            file = None  # Initialize file to None to handle cases where no image is available
            if google_street_view_api_key != "YOUR_API_KEY":
                street_view_base_url = "https://maps.googleapis.com/maps/api/staticmap"
                street_view_params = {
                    "size": "600x400",
                    "zoom": "13",
                    "scale": "2",  # Image size (width x height)
                    "center": f"{data1['latitude']},{data1['longitude']}",  # Latitude and Longitude as comma-separated string
                    "maptype": "hybrid",
                    "key": google_street_view_api_key
                }
                street_view_response = requests.get(street_view_base_url, params=street_view_params)
                if street_view_response.status_code == 200:
                    # Save the raw binary that the API returns as an image to set in embed.set_image
                    street_view_image_url = "attachment://street_view_image.jpg"
                    embed.set_image(url=street_view_image_url)
                    street_view_image_stream = io.BytesIO(street_view_response.content)
                    file = discord.File(fp=street_view_image_stream, filename="street_view_image.jpg")
                else:
                    # Handle the error accordingly, e.g., log it or send a message to the user
                    pass

            view = discord.ui.View(timeout=180)  # Initialize view outside of the else block
            if 'error' in data1:
                embed.add_field(name="Error", value=data1['error'], inline=False)
            elif not data1 or 'name' not in data1:
                embed.add_field(name="Error", value="No airport found with the provided code.", inline=False)
            else:
                for field, name in fields.items():
                    if field in data1 and field != 'link':
                        value = f"`{data1[field]}`"
                        embed.add_field(name=name, value=value, inline=False)
                
                # Check if 'link' is in data1 and add it to the view
                if 'link' in data1:
                    link = data1['link']
                    if not (link.startswith('http://') or link.startswith('https://')):
                        link = 'https://www.airport-data.com' + link
                    # URL button
                    view_airport = discord.ui.Button(label="View airport on airport-data.com", url=link, style=discord.ButtonStyle.link)
                    view.add_item(view_airport)

            # Send the message with the embed, view, and file (if available)
            await ctx.send(embed=embed, view=view, file=file)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @airport_group.command(name='runway')
    async def runwayinfo(self, ctx, code: str):
        """Query runway information by ICAO code."""
        if len(code) != 4:
            embed = discord.Embed(title="Error", description="Invalid ICAO code. ICAO codes are 4 characters long.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        try:
            api_token = await self.bot.get_shared_api_tokens("airportdbio")
            if api_token and 'api_token' in api_token:
                url2 = f"https://airportdb.io/api/v1/airport/{code}?apiToken={api_token['api_token']}"
                response2 = requests.get(url2)
                data2 = response2.json()

                if 'error' in data2:
                    error_message = data2['error']
                    if len(error_message) > 1024:
                        error_message = error_message[:1021] + "..."
                    embed = discord.Embed(title="Error", value=error_message, color=0xff4545)
                    await ctx.send(embed=embed)
                elif not data2 or 'name' not in data2:
                    embed = discord.Embed(title="Error", value="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                else:
                    combined_pages = []
                    if 'runways' in data2:
                        embed = discord.Embed(title=f"Runway information for {code.upper()}", color=0xfffffe)
                        runways = data2['runways']
                        for runway in runways:
                            if 'id' in runway:
                                embed.add_field(name="Runway ID", value=f"`{runway['id']}`", inline=True)

                            if 'surface' in runway:
                                embed.add_field(name="Surface", value=f"`{runway['surface']}`", inline=True)

                            if 'length_ft' in runway and 'width_ft' in runway:
                                embed.add_field(name="Dimensions", value=f"`{runway['length_ft']}ft long`\n`{runway['width_ft']}ft wide`", inline=True)

                            if 'le_ident' in runway or 'he_ident' in runway:
                                ils_value = ""
                                if 'le_ident' in runway:
                                    ils_info = runway.get('le_ils', {})
                                    ils_freq = ils_info.get('freq', 'N/A')
                                    ils_course = ils_info.get('course', 'N/A')
                                    ils_value += f"**{runway['le_ident']}** `{ils_freq} MHz @ {ils_course}°`\n"
                                if 'he_ident' in runway:
                                    ils_info = runway.get('he_ils', {})
                                    ils_freq = ils_info.get('freq', 'N/A')
                                    ils_course = ils_info.get('course', 'N/A')
                                    ils_value += f"**{runway['he_ident']}** `{ils_freq} MHz @ {ils_course}°`\n"
                                embed.add_field(name="Landing assistance", value=ils_value.strip(), inline=False)

                            runway_status = ":white_check_mark: **Open**" if str(runway.get('closed', 0)) == '0' else ":x: **Closed**"
                            embed.add_field(name="Runway status", value=runway_status, inline=True)

                            lighted_status = ":bulb: **Lighted**" if str(runway.get('lighted', 0)) == '1' else ":x: **Not Lighted**"
                            embed.add_field(name="Lighting", value=lighted_status, inline=True)

                            combined_pages.append(embed)
                            embed = discord.Embed(title=f"Runway information for {code.upper()}", color=0xfffffe)

                    await self.paginate_embed(ctx, combined_pages)
            else:
                embed = discord.Embed(title="Error", description="API token for airportdb.io not configured.", color=0xff4545)
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    async def paginate_embed(self, ctx, pages):
        message = await ctx.send(embed=pages[0])
        await message.add_reaction("⬅️")
        await message.add_reaction("❌")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"]

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
                break



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
                                    # Send the new alert
                                    await self._send_aircraft_info(alert_channel, {'ac': [aircraft_info]})
                                else:
                                    print(f"Error: Alert channel not found for guild {guild.name}")
                            else:
                                print(f"Error: No alert channel set for guild {guild.name}")
                await asyncio.sleep(2)  # Add a delay to respect API rate limit
        except Exception as e:
            print(f"Error checking emergency squawks: {e}")

    @check_emergency_squawks.before_loop
    async def before_check_emergency_squawks(self):
        await self.bot.wait_until_ready()  # Removed unnecessary try-except block

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        auto_icao = await self.config.guild(message.guild).auto_icao()
        if not auto_icao:
            return

        content = message.content
        icao_pattern = re.compile(r'^[a-fA-F0-9]{6}$')

        if icao_pattern.match(content):
            ctx = await self.bot.get_context(message)
            await self.aircraft_by_icao(ctx, content)

    def cog_unload(self):
        try:
            self.check_emergency_squawks.cancel()
        except Exception as e:
            print(f"Error unloading cog: {e}")
