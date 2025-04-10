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
from datetime import datetime
from moviepy import VideoFileClip
import tempfile
import os

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
            raise commands.UserFeedbackCheckFailure("Failed to fetch media from the URL.") from error

    async def get_dominant_color(self, image_url: str) -> discord.Color:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    response.raise_for_status()
                    image_data = await response.read()
                    color_thief = ColorThief(io.BytesIO(image_data))
                    dominant_color = color_thief.get_color(quality=1)
                    return discord.Color.from_rgb(*dominant_color)
        except Exception as e:
            logging.exception("Error fetching dominant color from image: %s", image_url, exc_info=e)
            raise RuntimeError("Failed to fetch dominant color from the image.") from e

    async def download_and_convert_to_audio(self, video_url: str) -> str:
        """Download the video and convert it to an audio file, returning the URL of the uploaded audio."""
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"Failed to download video, status code: {response.status}")

                video_data = await response.read()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
                    video_file.write(video_data)
                    video_file_path = video_file.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                    audio_file_path = audio_file.name

                # Use moviepy to extract audio
                try:
                    with VideoFileClip(video_file_path) as video_clip:
                        audio_clip = video_clip.audio
                        audio_clip.write_audiofile(audio_file_path)
                except Exception as e:
                    os.remove(video_file_path)  # Ensure video file is removed even if conversion fails
                    raise e

                os.remove(video_file_path)  # Clean up the video file after conversion

                # Upload the audio file using aiohttp
                try:
                    with open(audio_file_path, 'rb') as f:
                        async with session.post('https://temp.sh/upload', data={'file': f}) as upload_response:
                            upload_response.raise_for_status()
                            audio_url = await upload_response.text()
                            audio_url = audio_url.strip()
                finally:
                    os.remove(audio_file_path)  # Clean up the audio file after uploading

                return audio_url

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Automatically identify a song from an audio or video URL or uploaded file."""

        urls = []
        for attachment in message.attachments:
            if attachment.content_type and (attachment.content_type.startswith('audio/') or attachment.content_type.startswith('video/')):
                urls.append(attachment.url)

        if not urls:
            return

        async with message.channel.typing():
            for url in urls:
                try:
                    if url.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        media_url = await self.download_and_convert_to_audio(url)
                        media = await self.__aio_get(media_url)
                    else:
                        media = await self.__aio_get(url)

                    track_info = await self.alchemist.recognize(media)

                    if track_info and 'track' in track_info:
                        track = track_info['track']
                        share_text = track.get('share', {}).get('text', 'Unknown Title')
                        coverart_url = track.get('images', {}).get('coverart', '')
                        embed_color = await self.get_dominant_color(coverart_url) if coverart_url else discord.Color.blue()

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
                            except ValueError as ve:
                                logging.exception("Error parsing release date: %s", release_date_str, exc_info=ve)
                                raise RuntimeError("Failed to parse release date.") from ve

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
                    raise RuntimeError("An error occurred while processing the message.") from e
