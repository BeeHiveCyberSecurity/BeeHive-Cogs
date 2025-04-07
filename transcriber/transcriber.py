import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import aiohttp
from typing import Optional
import time
import tempfile
import os  # Import os for file operations

class Transcriber(commands.Cog):
    """Cog to transcribe voice notes using OpenAI."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=11111111, force_registration=True)
        default_guild = {
            "default_model": "whisper-1",
            "model_usage": {"gpt-4o-transcribe": 0, "gpt-4o-mini-transcribe": 0, "whisper-1": 0},
            "logging_channel": None,
            "moderation_enabled": True
        }
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
        """
        Specify an AI model to use for transcription

        You can choose between the following models

        - **whisper-1**
        > Cost efficient for use in large servers
        - **gpt-4o-mini-transcribe**
        > Faster, more intelligent, more expensive
        - **gpt-4o-transcribe**
        > High performance, high cost, high accuracy

        """
        valid_models = ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"]
        if model not in valid_models:
            await ctx.send(f"Invalid model. Choose from: {', '.join(valid_models)}.")
            return

        # Get the current model before changing
        current_model = await self.get_default_model(ctx.guild.id)
        
        # Update the model
        await self.config.guild(ctx.guild).default_model.set(model)

        # Get model details
        model_details = {
            "gpt-4o-transcribe": {
                "description": "[gpt-4o-transcribe](<https://platform.openai.com/docs/models/gpt-4o-transcribe>) is a speech-to-text model that uses [GPT-4o](<https://platform.openai.com/docs/models/gpt-4o>) to transcribe audio. It offers improvements to word error rate and better language recognition and accuracy compared to original Whisper models. Use `gpt 4o transcribe` to get the longest context window at the highest comparable prices for input and output.",
                "pricing": {
                    "input": "**$6.00** / **1,000,000 tokens**",
                    "output": "**$10.00** / **1,000,000 tokens**"
                },
                "performance": ":white_circle: :white_circle: :white_circle: :white_circle:",
                "speed": ":zap: :zap: :zap:"
            },
            "gpt-4o-mini-transcribe": {
                "description": "[gpt-4o-mini-transcribe](<https://platform.openai.com/docs/models/gpt-4o-mini-transcribe>) is a speech-to-text model that uses [GPT-4o mini](<https://platform.openai.com/docs/models/gpt-4o-mini>) to transcribe audio. It offers improvements to word error rate and better language recognition and accuracy compared to original Whisper models. `mini` models provide a balance of accuracy and cost-saving with the usage of frontier models, in comparison to their full-size and full-feature master model.",
                "pricing": {
                    "input": "**$3.00** / **1,000,000 tokens**",
                    "output": "**$5.00** / **1,000,000 tokens**"
                },
                "performance": ":white_circle: :white_circle: :white_circle:",
                "speed": ":zap: :zap: :zap: :zap:"
            },
            "whisper-1": {
                "description": "[whisper-1](<https://platform.openai.com/docs/models/whisper-1>) is a general-purpose speech recognition model, trained on a large dataset of diverse audio. You can also use it as a multitask model to perform multilingual speech recognition as well as speech translation and language identification. Use `whisper-1` for affordable, reliable transcription.",
                "pricing": {
                    "input": "**$0.006** / **1,000,000 tokens**",
                    "output": "Not priced"
                },
                "performance": ":white_circle: :white_circle:",
                "speed": ":zap: :zap: :zap:"
            }
        }

        # Get details for the current and new model
        current_details = model_details.get(current_model, {})
        new_details = model_details.get(model, {})

        # Create an embed to show the change
        embed = discord.Embed(title="Model updated", description="The model used for voice note transcription has been changed. See important details below.", color=0xfffffe)
        embed.add_field(name="Model", value=f" {current_model.replace('-', ' ')} -> {model.replace('-', ' ')}", inline=False)
        embed.add_field(name="Description", value=f"**Before:** {current_details.get('description', 'No description available')}\n\n**After:** {new_details.get('description', 'No description available')}", inline=False)
        embed.add_field(name="Pricing", value=f"**Before:**\n**`Input`** {current_details.get('pricing', {}).get('input', 'Not priced')}\n**`Output`** {current_details.get('pricing', {}).get('output', 'Not priced')}\n\n**After:**\n**`Input`** {new_details.get('pricing', {}).get('input', 'Not priced')}\n**`Output`** {new_details.get('pricing', {}).get('output', 'Not priced')}", inline=False)
        embed.add_field(name="Performance", value=f"{current_details.get('performance', 'Not rated')} -> {new_details.get('performance', 'Not rated')}", inline=True)
        embed.add_field(name="Speed", value=f"{current_details.get('speed', 'Not rated')} -> {new_details.get('speed', 'Not rated')}", inline=True)

        await ctx.send(embed=embed)

    @transcriber_group.command(name="settings")
    async def show_settings(self, ctx: commands.Context):
        """Show the current transcription settings for this server."""
        default_model = await self.get_default_model(ctx.guild.id)
        moderation_enabled = await self.config.guild(ctx.guild).moderation_enabled()
        
        # Define model details
        model_details = {
            "gpt-4o-transcribe": {
                "description": "[gpt-4o-transcribe](<https://platform.openai.com/docs/models/gpt-4o-transcribe>) is a speech-to-text model that uses [GPT-4o](<https://platform.openai.com/docs/models/gpt-4o>) to transcribe audio. It offers improvements to word error rate and better language recognition and accuracy compared to original Whisper models. Use `gpt 4o transcribe` to get the longest context window at the highest comparable prices for input and output.",
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
                "description": "[gpt-4o-mini-transcribe](<https://platform.openai.com/docs/models/gpt-4o-mini-transcribe>) is a speech-to-text model that uses [GPT-4o mini](<https://platform.openai.com/docs/models/gpt-4o-mini>) to transcribe audio. It offers improvements to word error rate and better language recognition and accuracy compared to original Whisper models. `mini` models provide a balance of accuracy and cost-saving with the usage of frontier models, in comparison to their full-size and full-feature master model.",
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
                "description": "[whisper-1](<https://platform.openai.com/docs/models/whisper-1>) is a general-purpose speech recognition model, trained on a large dataset of diverse audio. You can also use it as a multitask model to perform multilingual speech recognition as well as speech translation and language identification. Use `whisper-1` for affordable, reliable transcription.",
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
        highest_role_color = ctx.author.top_role.color if ctx.author.top_role.color else 0xfffffe
        embed = discord.Embed(title="Transcriber settings", color=highest_role_color)
        embed.add_field(name="Model in use", value=f"**{default_model.replace('-', ' ')}**", inline=False)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Context window", value=context_window, inline=True)
        embed.add_field(name="Maximum output", value=f"{max_output}", inline=True)
        embed.add_field(name="Model cost", value=f"**`Input`** {input_cost}\n**`Output`** {output_cost}", inline=False)
        embed.add_field(name="Model performance", value=f"{performance}", inline=True)
        embed.add_field(name="Model speed", value=f"{speed}", inline=True)
        embed.add_field(name="Knowledge cutoff", value=f"{knowledge_cutoff}", inline=True)
        embed.add_field(name="Real-time moderation", value="Enabled" if moderation_enabled else "Disabled", inline=True)
        
        await ctx.send(embed=embed)

    @transcriber_group.command(name="stats")
    async def show_stats(self, ctx: commands.Context):
        """Show the number of voice notes processed by each model in this server."""
        model_usage = await self.config.guild(ctx.guild).model_usage()
        embed = discord.Embed(title="Transcriber model usage", color=0xfffffe)
        for model, count in model_usage.items():
            embed.add_field(name=model, value=f"{count} voice notes", inline=False)
        await ctx.send(embed=embed)

    @transcriber_group.command(name="logs")
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where moderated voice notes and alerts are sent."""
        await self.config.guild(ctx.guild).logging_channel.set(channel.id)
        await ctx.send(f"Logging channel set to {channel.mention}")

    @transcriber_group.command(name="moderation")
    async def toggle_moderation(self, ctx: commands.Context):
        """Toggle the moderation feature on or off."""
        current_state = await self.config.guild(ctx.guild).moderation_enabled()
        new_state = not current_state
        await self.config.guild(ctx.guild).moderation_enabled.set(new_state)
        state_str = "enabled" if new_state else "disabled"
        await ctx.send(f"Moderation has been {state_str}.")

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
                if attachment.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac' '.mpeg', '.m4a')):
                    # Download the voice note
                    voice_note = await attachment.read()

                    try:
                        # Indicate that transcription is in progress
                        async with message.channel.typing():
                            # Get the default model for the server
                            default_model = await self.get_default_model(message.guild.id)

                            # Start timing the transcription process
                            transcription_start_time = time.monotonic()

                            # Send the voice note to OpenAI for transcription
                            transcription = await self.transcribe_voice_note(voice_note, attachment.content_type, default_model)

                            # Calculate the time taken for transcription
                            transcription_end_time = time.monotonic()
                            transcription_time = transcription_end_time - transcription_start_time

                            # Check if moderation is enabled
                            moderation_enabled = await self.config.guild(message.guild).moderation_enabled()

                            if moderation_enabled:
                                # Start timing the moderation process
                                moderation_start_time = time.monotonic()

                                # Send the transcription to the moderation endpoint
                                flagged, flags = await self.moderate_transcription(transcription)
                                if flagged:
                                    # Delete the message if flagged
                                    await message.delete()
                                    # Log the moderated voice note
                                    await self.log_moderation(message, voice_note, flags)
                                    return

                                # Calculate the time taken for moderation
                                moderation_end_time = time.monotonic()
                                moderation_time = moderation_end_time - moderation_start_time
                                moderation_time_display = f"{moderation_time * 1000:.2f} ms" if moderation_time < 1 else f"{moderation_time:.2f} seconds"
                            else:
                                moderation_time_display = "is disabled"

                            # Convert transcription time to human-readable format
                            transcription_time_display = f"{transcription_time * 1000:.2f} ms" if transcription_time < 1 else f"{transcription_time:.2f} seconds"

                            # Update model usage stats
                            async with self.config.guild(message.guild).model_usage() as model_usage:
                                model_usage[default_model] += 1

                    except ValueError as e:
                        await message.reply(f"Error during transcription: {str(e)}")
                        return

                    # Create embeds with the transcription
                    highest_role_color = message.author.top_role.color if message.author.top_role.color else discord.Color.default()
                    embeds = []
                    max_length = 4096
                    for i in range(0, len(transcription), max_length):
                        embed = discord.Embed(title="", description=transcription[i:i+max_length], color=highest_role_color)
                        embed.set_author(name=f"{message.author.display_name} said...", icon_url=message.author.avatar.url)
                        footer_text = f"{transcription_time_display} to transcribe"
                        if moderation_time_display != "is disabled":
                            footer_text += f", {moderation_time_display} to moderate"
                        footer_text += ". AI can make mistakes, double-check for accuracy"
                        embed.set_footer(text=footer_text)
                        embeds.append(embed)

                    # Reply to the message with the transcription
                    for embed in embeds:
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

    async def moderate_transcription(self, transcription: str) -> (bool, list):
        """Send the transcription to the moderation endpoint and return if it is flagged along with the flags."""
        url = "https://api.openai.com/v1/moderations"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        data = {
            "input": transcription
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise ValueError(f"Failed to moderate transcription: {response.status} - {error_message}")
                result = await response.json()
                flagged = result.get('results', [{}])[0].get('flagged', False)
                flags = result.get('results', [{}])[0].get('categories', {})
                # Sort flags by score and get the top 5
                sorted_flags = sorted(flags.items(), key=lambda item: item[1], reverse=True)[:5]
                return flagged, sorted_flags

    async def log_moderation(self, message: discord.Message, voice_note: bytes, flags: list):
        """Log the moderated voice note to the configured logging channel."""
        guild_config = await self.config.guild(message.guild).all()
        logging_channel_id = guild_config.get("logging_channel")
        if logging_channel_id:
            logging_channel = self.bot.get_channel(logging_channel_id)
            if logging_channel:
                embed = discord.Embed(
                    title="Voice note moderated",
                    description=f"A voice note from {message.author.mention} in {message.channel.mention} has been moderated.",
                    color=0xff4545
                )
                # Add the top 5 flags to the embed
                if flags:
                    flag_details = "\n".join([f"{flag}: {score:.2f}" for flag, score in flags])
                    embed.add_field(name="Scored categories", value=flag_details, inline=False)
                temp_file_path = None  # Initialize temp_file_path
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_file.write(voice_note)
                        temp_file_path = temp_file.name
                    await logging_channel.send(embed=embed, file=discord.File(temp_file_path, filename="moderated_voice_note.mp3"))
                except Exception as e:  # Catch all exceptions
                    await logging_channel.send(f"Failed to send moderated voice note: {str(e)}")
                finally:
                    if temp_file_path and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
