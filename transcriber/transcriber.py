import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import aiohttp
from typing import Optional
import time

class Transcriber(commands.Cog):
    """Cog to transcribe voice notes using OpenAI."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=11111111, force_registration=True)
        default_guild = {"default_model": "whisper-1"}
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
        valid_models = ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"]
        if model not in valid_models:
            await ctx.send(f"Invalid model. Choose from: {', '.join(valid_models)}.")
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
                "description": "GPT-4o Transcribe is a speech-to-text model that uses GPT-4o to transcribe audio. It offers improvements to word error rate and better language recognition and accuracy compared to original Whisper models. Use it for more accurate transcripts.",
                "pricing": {
                    "input": "**$6.00** / **1,000,000 tokens**",
                    "cached_input": "",
                    "output": "**$10.00** / **1,000,000 tokens**"
                },
                "context_window": "16,000 tokens",
                "performance": ":white_circle: :white_circle: :white_circle: :white_circle:",
                "speed": ":zap: :zap: :zap:",
                "max_output": "2,000 tokens",
                "knowledge_cutoff": "May 31, 2024"
            },
            "gpt-4o-mini-transcribe": {
                "description": "GPT-4o mini Transcribe is a speech-to-text model that uses GPT-4o mini to transcribe audio. It offers improvements to word error rate and better language recognition and accuracy compared to original Whisper models. Use it for more accurate transcripts.",
                "pricing": {
                    "input": "**$3.00** / **1,000,000 tokens**",
                    "cached_input": "",
                    "output": "**$5.00** / **1,000,000 tokens**"
                },
                "context_window": "16,000 tokens",
                "performance": ":white_circle: :white_circle: :white_circle:",
                "speed": ":zap: :zap: :zap: :zap:",
                "max_output": "2,000 tokens",
                "knowledge_cutoff": "May 31, 2024"
            },
            "whisper-1": {
                "description": "Whisper is a general-purpose speech recognition model, trained on a large dataset of diverse audio. You can also use it as a multitask model to perform multilingual speech recognition as well as speech translation and language identification.",
                "pricing": {
                    "input": "**$0.006** / **1,000,000 tokens**",
                    "cached_input": "",
                    "output": ""
                },
                "context_window": "",
                "performance": ":white_circle: :white_circle:",
                "speed": ":zap: :zap: :zap:",
                "max_output": "",
                "knowledge_cutoff": ""
            }
        }
        
        details = model_details.get(default_model, {})
        description = details.get("description", "No description available")
        pricing = details.get("pricing", {})
        input_cost = pricing.get("input") or "Not priced"
        output_cost = pricing.get("output") or "Not priced"
        context_window = details.get("context_window") or "Not available"
        max_output = details.get("max_output") or "Not provided"
        performance = details.get("performance") or "Not rated"
        speed = details.get("speed") or "Not rated"
        knowledge_cutoff = details.get("knowledge_cutoff") or "Not applicable"
        
        # Create an embed for the settings
        highest_role_color = ctx.author.top_role.color if ctx.author.top_role.color else discord.Color.default()
        embed = discord.Embed(title="Transcriber settings", color=highest_role_color)
        embed.add_field(name="Model in use", value=f"**{default_model.replace('-', ' ')}**", inline=False)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Context window", value=context_window, inline=True)
        embed.add_field(name="Maximum output", value=f"{max_output}", inline=True)
        embed.add_field(name="Model cost", value=f"**`Input`** {input_cost}\n**`Output`** {output_cost}", inline=False)
        embed.add_field(name="Model performance", value=f"{performance}", inline=True)
        embed.add_field(name="Model speed", value=f"{speed}", inline=True)
        embed.add_field(name="Knowledge cutoff", value=f"{knowledge_cutoff}", inline=True)
        
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
                if attachment.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.mp4', '.mpeg', '.mpga', '.m4a', '.webm')):
                    # Download the voice note
                    voice_note = await attachment.read()

                    try:
                        # Indicate that transcription is in progress
                        async with message.channel.typing():
                            # Get the default model for the server
                            default_model = await self.get_default_model(message.guild.id)

                            # Start timing the transcription process
                            start_time = time.monotonic()

                            # Send the voice note to OpenAI for transcription
                            transcription = await self.transcribe_voice_note(voice_note, attachment.content_type, default_model)

                            # Calculate the time taken for transcription
                            end_time = time.monotonic()
                            transcription_time = end_time - start_time

                            # Convert transcription time to human-readable format
                            if transcription_time < 1:
                                time_display = f"{transcription_time * 1000:.2f} ms"
                            elif transcription_time < 60:
                                time_display = f"{transcription_time:.2f} seconds"
                            else:
                                minutes, seconds = divmod(transcription_time, 60)
                                time_display = f"{int(minutes)} minutes and {seconds:.2f} seconds"
                    except ValueError as e:
                        await message.reply(f"Error during transcription: {str(e)}")
                        return

                    # Create an embed with the transcription
                    highest_role_color = message.author.top_role.color if message.author.top_role.color else discord.Color.default()
                    embed = discord.Embed(title="", description=transcription, color=highest_role_color)
                    embed.set_author(name=f"{message.author.display_name} said...", icon_url=message.author.avatar.url)
                    embed.set_footer(text=f"Transcribed using AI in {time_display}, check results for accuracy")

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
                return result.get('text', 'Transcription failed: No text returned')
