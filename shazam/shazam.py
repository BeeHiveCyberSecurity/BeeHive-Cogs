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
import ffmpeg
import tempfile

class ShazamCog(commands.Cog):
    """Cog to interact with the Shazam API using shazamio."""

    def __init__(self, bot):
        self.bot = bot
        self.alchemist: AudioAlchemist = AudioAlchemist()

    async def __aio_get(self, url: str) -> bytes:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=120.0) as response:
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
            return discord.Color(0xfffffe)

    async def extract_audio_from_video(self, video_bytes: bytes) -> bytes:
        """Extract audio from video bytes using ffmpeg."""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_video, tempfile.NamedTemporaryFile(delete=False) as temp_audio:
                temp_video.write(video_bytes)
                temp_video.flush()

                input_stream = ffmpeg.input(temp_video.name)
                output_stream = ffmpeg.output(input_stream, temp_audio.name, format='mp3', acodec='libmp3lame')
                ffmpeg.run(output_stream)

                with open(temp_audio.name, 'rb') as audio_file:
                    audio_bytes = audio_file.read()

            return audio_bytes
        except Exception as e:
            logging.exception("Error extracting audio from video", exc_info=e)
            raise commands.UserFeedbackCheckFailure("Failed to extract audio from the video.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Automatically identify a song from an audio or video URL or uploaded file."""
        if message.author.bot:
            return

        urls = []
        for attachment in message.attachments:
            if attachment.content_type and (attachment.content_type.startswith('audio/') or attachment.content_type.startswith('video/')):
                urls.append(attachment.url)

        if not urls:
            return

        async with message.channel.typing():
            for url in urls:
                try:
                    media: bytes = await self.__aio_get(url)
                    
                    # Check if the file is a video and extract audio if necessary
                    if 'video/' in url:
                        media = await self.extract_audio_from_video(media)

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
                            release_date_str = metadata[2].get('text', '') if len(metadata) > 2 else ''

                        # Convert release date to discord dynamic timestamp
                        release_date_timestamp = ''
                        if release_date_str:
                            try:
                                if len(release_date_str) == 4:  # Year only
                                    release_date = datetime.strptime(release_date_str, '%Y')
                                else:
                                    release_date = datetime.strptime(release_date_str, '%d-%m-%Y')
                                release_date_timestamp = f"<t:{int(release_date.timestamp())}:D>"
                            except ValueError:
                                release_date_timestamp = release_date_str

                        description = f"{genre}"
                        if release_date_str:  # Ensure release date is shown when available
                            description += f", released {release_date_timestamp}"

                        embed = discord.Embed(
                            title=share_text,
                            description=description,
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
                        apple_music_option = track.get('hub', {}).get('options', [{}])[0]
                        apple_music_url = apple_music_option.get('actions', [{}])[0].get('uri', '')

                        if shazam_url:
                            shazam_button = discord.ui.Button(label="Listen on Shazam", url=shazam_url)
                            view.add_item(shazam_button)

                        # Ensure the Apple Music URL is valid
                        if apple_music_url.startswith(('http://', 'https://')):
                            apple_music_button = discord.ui.Button(label="Open in Apple Music", url=apple_music_url)
                            view.add_item(apple_music_button)

                        # Send the embed without the JSON file
                        await message.reply(embed=embed, view=view)
                except Exception as e:
                    logging.exception("Error processing message: %s", message.content, exc_info=e)
                    embed = discord.Embed(
                        title="Error",
                        description=f"An error occurred: {str(e)}",
                        color=discord.Color.red()
                    )
                    await message.reply(embed=embed)
