import asyncio
import logging
from typing import Union, Dict, Any
import discord
import aiohttp
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
            log.exception("Error fetching media from URL: %s", url, exc_info=error)
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
                track_info: Dict[str, Any] = await self.alchemist.recognize(media)

                if track_info:
                    serialized_info = Shazamalize.full_track(track_info)
                    track_title = serialized_info['track']['title']
                    track_artist = serialized_info['track']['subtitle']
                    embed = discord.Embed(
                        title="Song Identified",
                        description=f"**Title:** {track_title}\n**Artist:** {track_artist}",
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title="Song Not Identified",
                        description="Could not identify the song from the provided URL or file.",
                        color=discord.Color.red()
                    )
            except Exception as e:
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed)
