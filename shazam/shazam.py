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

    @commands.command(name="identify")
    async def identify_song(self, ctx: commands.Context, url: str = None):
        """Identify a song from an audio URL or uploaded file."""
        if not url and not ctx.message.attachments:
            await ctx.send("Please provide a URL or upload an audio file.", delete_after=10)
            return

        async with ctx.typing():
            try:
                if ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    url = attachment.url

                media: bytes = await self.__aio_get(url)
                track_info = await self.alchemist.recognize(media)

                if track_info and 'track' in track_info:
                    track = track_info['track']
                    share_text = track.get('share', {}).get('text', 'Unknown Title')
                    coverart_url = track.get('images', {}).get('coverart', '')
                    embed_color = self.get_dominant_color(coverart_url) if coverart_url else discord.Color.blue()

                    genre = track.get('genres', {}).get('primary', 'N/A')

                    embed = discord.Embed(
                        title=share_text,
                        description=f"`{genre}`",
                        color=embed_color
                    )
                    embed.set_thumbnail(url=coverart_url)

                    # Safely access metadata fields
                    sections = track_info.get('sections', [{}])
                    metadata = sections[0].get('metadata', []) if sections else []

                    # Check for explicit content
                    if track.get('explicit', False):
                        embed.set_footer(text="Song contains explicit content, audience discretion advised")

                    # Add additional fields from the track_info
                    embed.add_field(name="Track ID", value=track.get('key', 'N/A'), inline=True)
                    embed.add_field(name="ISRC", value=track.get('isrc', 'N/A'), inline=True)

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
                    await ctx.send(embed=embed, file=json_file, view=view)
                else:
                    embed = discord.Embed(
                        title="Identification Failed",
                        description="Could not identify the song from the provided URL or file.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
