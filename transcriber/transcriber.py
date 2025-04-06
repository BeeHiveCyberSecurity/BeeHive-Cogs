import discord
from redbot.core import commands
from redbot.core.bot import Red
import aiohttp
from typing import Optional
import tempfile

class Transcriber(commands.Cog):
    """Cog to transcribe voice notes using OpenAI."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.openai_api_key: Optional[str] = None

    async def cog_load(self):
        # Load the OpenAI API key from the bot's configuration
        tokens = await self.bot.get_shared_api_tokens("openai")
        self.openai_api_key = tokens.get("api_key")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set. Please set it using the bot's configuration.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message contains an attachment and if it's a voice note
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(('.mp3', '.wav', '.ogg')):
                    # Download the voice note
                    voice_note = await attachment.read()

                    # Send the voice note to OpenAI for transcription
                    transcription = await self.transcribe_voice_note(voice_note, attachment.content_type)

                    # Create an embed with the transcription
                    embed = discord.Embed(title="Transcription", description=transcription, color=discord.Color.blue())
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)

                    # Reply to the message with the transcription
                    await message.reply(embed=embed)

    async def transcribe_voice_note(self, voice_note: bytes, content_type: Optional[str]) -> str:
        # This function should handle sending the voice note to OpenAI and returning the transcription
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(voice_note)
            temp_file_name = temp_file.name

        data = aiohttp.FormData()
        data.add_field('file', open(temp_file_name, 'rb'), filename='audio.mp3', content_type=content_type or "audio/mpeg")
        data.add_field('model', 'gpt-4o-transcribe')

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to transcribe audio: {response.status}")
                result = await response.json()
                return result['text']
