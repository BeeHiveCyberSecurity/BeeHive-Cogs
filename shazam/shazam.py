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
                    embed = discord.Embed(
                        title=track.get('title', 'Unknown Title'),
                        description=f"Artist: {track.get('subtitle', 'Unknown Artist')}",
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=track.get('images', {}).get('coverart', ''))

                    # Safely access metadata fields
                    sections = track_info.get('sections', [{}])
                    metadata = sections[0].get('metadata', []) if sections else []

                    album = metadata[0].get('text', 'N/A') if len(metadata) > 0 else 'N/A'
                    label = metadata[1].get('text', 'N/A') if len(metadata) > 1 else 'N/A'
                    released = metadata[2].get('text', 'N/A') if len(metadata) > 2 else 'N/A'

                    embed.add_field(name="Album", value=album, inline=True)
                    embed.add_field(name="Label", value=label, inline=True)
                    embed.add_field(name="Released", value=released, inline=True)
                    embed.add_field(name="Genre", value=track.get('genres', {}).get('primary', 'N/A'), inline=True)

                    # Check for explicit content
                    if track.get('explicit', False):
                        embed.set_footer(text="Song contains explicit content, audience discretion advised")
                    else:
                        continue

                    # Add additional fields from the track_info
                    embed.add_field(name="Track ID", value=track_info.get('track', {}).get('key', 'N/A'), inline=True)
                    embed.add_field(name="ISRC", value=track_info.get('track', {}).get('isrc', 'N/A'), inline=True)

                    # Create URL buttons for Shazam and Apple Music
                    view = discord.ui.View()
                    shazam_url = track.get('url', '')
                    apple_music_url = track_info.get('track', {}).get('hub', {}).get('actions', [{}])[0].get('uri', '')

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
