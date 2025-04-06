import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import aiohttp
from typing import Optional

class Transcriber(commands.Cog):
    """Cog to transcribe voice notes using OpenAI."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"default_model": "gpt-4o-mini-transcribe"}
        self.config.register_guild(**default_guild)
        self.openai_api_key: Optional[str] = None

    async def cog_load(self):
        # Load the OpenAI API key from the bot's configuration
        tokens = await self.bot.get_shared_api_tokens("openai")
        self.openai_api_key = tokens.get("api_key")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set. Please set it using the bot's configuration.")

    @commands.group(name="transcriber", invoke_without_command=True)
    @commands.guild_only()
    @commands.admin_or_permissions()
    async def transcriber_group(self, ctx: commands.Context):
        """Group command for transcriber related commands."""
        await ctx.send_help(ctx.command)

    @transcriber_group.command(name="model")
    async def set_model(self, ctx: commands.Context, model: str):
        """Choose an AI model to use for transcription requests"""
        if model not in ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"]:
            await ctx.send("Invalid model. Choose from: gpt-4o-transcribe, gpt-4o-mini-transcribe, whisper-1.")
            return
        await self.config.guild(ctx.guild).default_model.set(model)
        await ctx.send(f"Default transcription model set to: {model} for this server.")

    @transcriber_group.command(name="settings")
    async def show_settings(self, ctx: commands.Context):
        """Show the current transcription settings for this server."""
        default_model = await self.get_default_model(ctx.guild.id)
        
        # Define model details
        model_details = {
            "gpt-4o-transcribe": {
                "token_cost": "$2.50 per 1M tokens",
                "context_cap": "8K tokens"
            },
            "gpt-4o-mini-transcribe": {
                "token_cost": "0.03 per 1K tokens",
                "context_cap": "4K tokens"
            },
            "whisper-1": {
                "token_cost": "0.02 per 1K tokens",
                "context_cap": "2K tokens"
            }
        }
        
        details = model_details.get(default_model, {})
        token_cost = details.get("token_cost", "N/A")
        context_cap = details.get("context_cap", "N/A")
        
        # Create an embed for the settings
        embed = discord.Embed(title="Transcriber settings", color=0xfffffe)
        embed.add_field(name="Model in use", value=default_model, inline=True)
        embed.add_field(name="Token cost", value=token_cost, inline=True)
        embed.add_field(name="Context cap", value=context_cap, inline=True)
        
        await ctx.send(embed=embed)

    async def get_default_model(self, guild_id: int) -> str:
        """Retrieve the default model for a specific server."""
        return await self.config.guild_from_id(guild_id).default_model()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message contains an attachment and if it's a voice note
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(('.mp3', '.wav', '.ogg', '.flac', '.mp4', '.mpeg', '.mpga', '.m4a', '.webm')):
                    # Download the voice note
                    voice_note = await attachment.read()

                    try:
                        # Indicate that transcription is in progress
                        async with message.channel.typing():
                            # Get the default model for the server
                            default_model = await self.get_default_model(message.guild.id)

                            # Send the voice note to OpenAI for transcription
                            transcription = await self.transcribe_voice_note(voice_note, attachment.content_type, default_model)
                    except ValueError as e:
                        await message.reply(f"Error during transcription: {str(e)}")
                        return

                    # Create an embed with the transcription
                    embed = discord.Embed(title="", description=transcription, color=0xfffffe)
                    embed.set_author(name=f"{message.author.display_name} said...", icon_url=message.author.avatar.url)
                    embed.set_footer(text="Transcribed using AI, check results for accuracy")

                    # Reply to the message with the transcription
                    await message.reply(embed=embed)

    async def transcribe_voice_note(self, voice_note: bytes, content_type: Optional[str], model: str) -> str:
        # This function should handle sending the voice note to OpenAI and returning the transcription
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}"
        }

        data = aiohttp.FormData()
        data.add_field('file', voice_note, filename='audio', content_type=content_type or "audio/mpeg")
        data.add_field('model', model)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise ValueError(f"Failed to transcribe audio: {response.status} - {error_message}")
                result = await response.json()
                return result['text']
