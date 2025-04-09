import asyncio
import logging
import json
from typing import Union, Dict, Any
import discord
import aiohttp
import io
from aiohttp_retry import ExponentialRetry as Pulse
from redbot.core import commands
from shazamio.api import Shazam as AudioAlchemist
from shazamio.serializers import Serialize as Shazamalize
from colorthief import ColorThief
import requests
from datetime import datetime

class ShazamCog(commands.Cog):
    """Cog to interact with the Shazam API using shazamio."""

    def __init__(self, bot):
        self.bot = bot
        self.alchemist: AudioAlchemist = AudioAlchemist()

    async def __aio_get(self, url: str) -> bytes:
        try:
            async with aiohttp.ClientSession() as session:
                response: aiohttp.ClientResponse = await session.get(url, timeout=120.0)
                response.raise_for_status()
                return await response.read()
        except aiohttp.ClientError as error:
            logging.exception("Error fetching media from URL: %s", url, exc_info=error)
            raise commands.UserFeedbackCheckFailure("Failed to fetch media from the URL.")

    def get_dominant_color(self, image_url: str) -> discord.Color:
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            color_thief = ColorThief(io.BytesIO(response.content))
            dominant_color = color_thief.get_color(quality=1)
            return discord.Color.from_rgb(*dominant_color)
        except Exception as e:
            logging.exception("Error fetching dominant color from image: %s", image_url, exc_info=e)
            return discord.Color.blue()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Automatically identify a song from an audio URL or uploaded file."""
        if message.author.bot:
            return

        url = None
        if message.attachments:
            attachment = message.attachments[0]
            url = attachment.url

        if not url:
            return

        async with message.channel.typing():
            try:
                media: bytes = await self.__aio_get(url)
                track_info = await self.alchemist.recognize(media)

                if track_info and 'track' in track_info:
                    track = track_info['track']
                    share_text = track.get('share', {}).get('text', 'Unknown Title')
                    coverart_url = track.get('images', {}).get('coverart', '')
                    embed_color = self.get_dominant_color(coverart_url) if coverart_url else discord.Color.blue()

                    genre = track.get('genres', {}).get('primary', 'N/A')
                    release_date_str = track.get('releasedate', '')

                    # Check if release date is available, otherwise use metadata
                    if not release_date_str or release_date_str == 'Unknown Release Date':
                        sections = track_info.get('sections', [{}])
                        metadata = sections[0].get('metadata', []) if sections else []
                        release_date_str = next((item['text'] for item in metadata if item['title'] == 'Released'), 'Unknown Release Date')

                    # Convert release date to discord dynamic timestamp
                    try:
                        if len(release_date_str) == 4:  # Year only
                            release_date = datetime.strptime(release_date_str, '%Y')
                        else:
                            release_date = datetime.strptime(release_date_str, '%d-%m-%Y')
                        release_date_timestamp = f"<t:{int(release_date.timestamp())}:D>"
                    except ValueError:
                        release_date_timestamp = release_date_str

                    embed = discord.Embed(
                        title=share_text,
                        description=f"Genre: {genre}\nRelease Date: {release_date_timestamp}",
                        color=embed_color
                    )
                    embed.set_thumbnail(url=coverart_url)

                    # Check for explicit content
                    hub_info = track.get('hub', {})
                    if hub_info.get('explicit', False):
                        embed.set_footer(text="Song contains explicit content, audience discretion advised")

                    # Create URL buttons for Shazam and Apple Music
                    view = discord.ui.View()
                    shazam_url = track.get('url', '')
                    apple_music_url = track.get('hub', {}).get('actions', [{}])[0].get('uri', '')

                    if shazam_url:
                        shazam_button = discord.ui.Button(label="Listen on Shazam", url=shazam_url)
                        view.add_item(shazam_button)

                    if apple_music_url:
                        apple_music_button = discord.ui.Button(label="Listen on Apple Music", url=apple_music_url)
                        view.add_item(apple_music_button)

                    # Convert track_info to JSON and send as a file
                    json_data = json.dumps(track_info, indent=4)
                    json_file = discord.File(fp=io.StringIO(json_data), filename="track_info.json")
                    await message.channel.send(embed=embed, file=json_file, view=view)
            except Exception as e:
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
