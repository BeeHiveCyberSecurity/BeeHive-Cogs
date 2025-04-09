import discord
from redbot.core import commands
import aiohttp
import tempfile
import os
from ffmpeg import video

class VideoToAudio(commands.Cog):
    """Cog to convert video messages to audio and reply with the audio file."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for video messages and convert them to audio."""
        if message.author.bot:
            return

        video_urls = [attachment.url for attachment in message.attachments if attachment.content_type and attachment.content_type.startswith('video/')]

        if not video_urls:
            return

        async with message.channel.typing():
            for video_url in video_urls:
                try:
                    audio_file_path = await self.download_and_convert_to_audio(video_url)
                    if audio_file_path:
                        await message.reply(file=discord.File(audio_file_path))
                        os.remove(audio_file_path)  # Clean up the audio file after sending
                except Exception as e:
                    await message.channel.send(f"An error occurred: {str(e)}")

    async def download_and_convert_to_audio(self, video_url: str) -> str:
        """Download the video and convert it to an audio file."""
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

                # Use ffmpeg to extract audio
                try:
                    video.ins_img(video_file_path, [], audio_file_path)
                except Exception as e:
                    os.remove(video_file_path)  # Ensure video file is removed even if conversion fails
                    raise e

                os.remove(video_file_path)  # Clean up the video file after conversion

                return audio_file_path
