import discord
from redbot.core import commands, Config
import aiohttp
from datetime import timedelta, datetime
from collections import Counter
import unicodedata
import re

class Omni(commands.Cog):
    """AI-powered automatic text moderation provided by frontier moderation models"""

    VERSION = "0.0.3"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(
            moderation_threshold=0.5,
            timeout_duration=0,
            log_channel=None,
            debug_mode=False,
            message_count=0,
            moderated_count=0,
            moderated_users=[],
            category_counter={},
            whitelisted_channels=[],
            cog_version=self.VERSION
        )
        self.session = None
        self.message_count = 0
        self.moderated_count = 0
        self.moderated_users = set()
        self.category_counter = Counter()

    async def initialize(self):
        try:
            self.session = aiohttp.ClientSession()
            all_guilds = await self.config.all_guilds()
            for guild_id, data in all_guilds.items():
                self.message_count = data.get("message_count", 0)
                self.moderated_count = data.get("moderated_count", 0)
                self.moderated_users = set(data.get("moderated_users", []))
                self.category_counter = Counter(data.get("category_counter", {}))
                
                # Check for version update
                stored_version = data.get("cog_version", "0.0.0")
                if stored_version != self.VERSION:
                    await self.config.guild_from_id(guild_id).cog_version.set(self.VERSION)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Omni cog: {e}")

    def normalize_text(self, text):
        """Normalize text to replace with standard alphabetical/numeric characters."""
        try:
            # Normalize to NFKD form and replace non-standard characters
            text = ''.join(
                c if unicodedata.category(c).startswith(('L', 'N')) else ' '
                for c in unicodedata.normalize('NFKD', text)
            )
            # Handle special words/characters
            text = text.replace('nègre', 'negro')
            # Replace multiple spaces with a single space
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            raise ValueError(f"Failed to normalize text: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.bot:
                return

            guild = message.guild
            if not guild:
                return

            # Check if the channel is whitelisted
            whitelisted_channels = await self.config.guild(guild).whitelisted_channels()
            if message.channel.id in whitelisted_channels:
                return

            self.message_count += 1
            await self.config.guild(guild).message_count.set(self.message_count)

            api_tokens = await self.bot.get_shared_api_tokens("openai")
            api_key = api_tokens.get("api_key")
            if not api_key:
                return

            # Ensure the session is open
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()

            # Normalize the message content
            normalized_content = self.normalize_text(message.content)

            # Analyze text content
            text_flagged, text_category_scores = await self.analyze_text(normalized_content, api_key, message)

            if text_flagged:
                self.moderated_count += 1
                await self.config.guild(guild).moderated_count.set(self.moderated_count)
                self.moderated_users.add(message.author.id)
                await self.config.guild(guild).moderated_users.set(list(self.moderated_users))
                for category, score in text_category_scores.items():
                    if score > 0:
                        self.category_counter[category] += 1
                await self.config.guild(guild).category_counter.set(dict(self.category_counter))
                await self.handle_moderation(message, text_category_scores)

            # Check if debug mode is enabled
            debug_mode = await self.config.guild(guild).debug_mode()
            if debug_mode:
                await self.log_message(message, text_category_scores)
        except Exception as e:
            raise RuntimeError(f"Error processing message: {e}")

    async def analyze_text(self, text, api_key, message):
        try:
            async with self.session.post(
                "https://api.openai.com/v1/moderations",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "omni-moderation-latest",
                    "input": [
                        {"type": "text", "text": text}
                    ]
                }
            ) as response:
                if response.status != 200:
                    # Log the error if the request failed
                    await self.log_message(message, {}, error_code=response.status)
                    return False, {}

                data = await response.json()
                result = data.get("results", [{}])[0]
                flagged = result.get("flagged", False)
                category_scores = result.get("category_scores", {})
                return flagged, category_scores
        except Exception as e:
            raise RuntimeError(f"Failed to analyze text: {e}")

    async def handle_moderation(self, message, category_scores):
        try:
            guild = message.guild
            timeout_duration = await self.config.guild(guild).timeout_duration()
            log_channel_id = await self.config.guild(guild).log_channel()

            # Delete the message
            try:
                await message.delete()
            except discord.NotFound:
                pass  # Handle cases where the message is already deleted

            # Timeout the user if duration is set
            if timeout_duration > 0:
                try:
                    await message.author.timeout(timedelta(minutes=timeout_duration), reason="Automated moderation action")
                except discord.Forbidden:
                    pass  # Handle cases where the bot doesn't have permission to timeout

            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="✨ Message moderated using AI",
                        description=f"A message was deleted from chat because it potentially violated the rules.",
                        color=0xff4545,
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Message content", value=f"||{message.content}||" or "No content", inline=False)
                    embed.add_field(name="Sender", value=f"{message.author}\n```{message.author.id}```", inline=False)
                    embed.add_field(name="Channel", value=f"{message.channel}\n```{message.channel.id}```", inline=False)
                    moderation_threshold = await self.config.guild(guild).moderation_threshold()
                    sorted_scores = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]
                    for category, score in sorted_scores:
                        if score == 0.00:
                            score_display = ":white_check_mark: Clean"
                        else:
                            score_display = f"**{score:.2f}**" if score > moderation_threshold else f"{score:.2f}"
                        embed.add_field(name=category.capitalize(), value=score_display, inline=True)
                    await log_channel.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to handle moderation: {e}")

    async def log_message(self, message, category_scores, error_code=None):
        try:
            guild = message.guild
            log_channel_id = await self.config.guild(guild).log_channel()

            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="AI screened a message and found no threat",
                        description=f"Message by {message.author.mention} was logged.",
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Content", value=message.content or "No content", inline=False)
                    embed.add_field(name="Sender", value=f"{message.author} (ID: {message.author.id})", inline=True)
                    embed.add_field(name="Channel", value=f"{message.channel} (ID: {message.channel.id})", inline=True)
                    moderation_threshold = await self.config.guild(guild).moderation_threshold()
                    sorted_scores = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]
                    for category, score in sorted_scores:
                        if score == 0.00:
                            score_display = ":white_check_mark: Clean"
                        else:
                            score_display = f"**{score:.2f}**" if score > moderation_threshold else f"{score:.2f}"
                        embed.add_field(name=category.capitalize(), value=score_display, inline=True)
                    if error_code:
                        embed.add_field(name="Error", value=f":x: Failed to send to OpenAI endpoint. Error code: {error_code}", inline=False)
                    await log_channel.send(embed=embed)
            else:
                # If no log channel is set, send a warning to the server owner
                owner = guild.owner
                if owner:
                    try:
                        await owner.send(
                            f"Warning: No log channel is set for the guild '{guild.name}'. "
                            "Please set a log channel using the `[p]omni logs` command to enable message logging."
                        )
                    except discord.Forbidden:
                        pass  # Handle cases where the bot doesn't have permission to DM the owner
        except Exception as e:
            raise RuntimeError(f"Failed to log message: {e}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def omni(self, ctx):
        """AI-powered automatic text moderation provided by frontier moderation models"""
        pass

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def threshold(self, ctx, threshold: float):
        """Set the moderation threshold (0 to 1)."""
        try:
            if 0 <= threshold <= 1:
                await self.config.guild(ctx.guild).moderation_threshold.set(threshold)
                await ctx.send(f"Moderation threshold set to {threshold}.")
            else:
                await ctx.send("Threshold must be between 0 and 1.")
        except Exception as e:
            raise RuntimeError(f"Failed to set threshold: {e}")

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def timeout(self, ctx, duration: int):
        """Set the timeout duration in minutes (0 for no timeout)."""
        try:
            if duration >= 0:
                await self.config.guild(ctx.guild).timeout_duration.set(duration)
                await ctx.send(f"Timeout duration set to {duration} minutes.")
            else:
                await ctx.send("Timeout duration must be 0 or greater.")
        except Exception as e:
            raise RuntimeError(f"Failed to set timeout duration: {e}")

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def logs(self, ctx, channel: discord.TextChannel):
        """Set the channel to log moderated messages."""
        try:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"Log channel set to {channel.mention}.")
        except Exception as e:
            raise RuntimeError(f"Failed to set log channel: {e}")

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def whitelist(self, ctx, channel: discord.TextChannel):
        """Add or remove a channel from the whitelist."""
        try:
            guild = ctx.guild
            whitelisted_channels = await self.config.guild(guild).whitelisted_channels()
            changelog = []

            if channel.id in whitelisted_channels:
                whitelisted_channels.remove(channel.id)
                changelog.append(f"Removed: {channel.mention}")
            else:
                whitelisted_channels.append(channel.id)
                changelog.append(f"Added: {channel.mention}")

            await self.config.guild(guild).whitelisted_channels.set(whitelisted_channels)

            if changelog:
                changelog_message = "\n".join(changelog)
                embed = discord.Embed(title="Whitelist Changelog", description=changelog_message, color=discord.Color.blue())
                await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to update whitelist: {e}")

    @omni.command()
    @commands.is_owner()
    async def debug(self, ctx):
        """Toggle debug mode to log all messages and their scores."""
        try:
            guild = ctx.guild
            current_debug_mode = await self.config.guild(guild).debug_mode()
            new_debug_mode = not current_debug_mode
            await self.config.guild(guild).debug_mode.set(new_debug_mode)
            status = "enabled" if new_debug_mode else "disabled"
            await ctx.send(f"Debug mode {status}.")
        except Exception as e:
            raise RuntimeError(f"Failed to toggle debug mode: {e}")

    @omni.command()
    async def stats(self, ctx):
        """Show statistics of the moderation activity."""
        try:
            top_categories = self.category_counter.most_common(5)
            top_categories_bullets = "\n".join([f"- {cat.capitalize()}: {count}" for cat, count in top_categories])
            
            embed = discord.Embed(title="✨ AI is hard at work for you", color=0xfffffe)
            embed.add_field(name="Messages processed", value=str(self.message_count), inline=True)
            embed.add_field(name="Messages moderated", value=str(self.moderated_count), inline=True)
            embed.add_field(name="Users punished", value=str(len(self.moderated_users)), inline=True)
            embed.add_field(name="Top violation categories", value=top_categories_bullets, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to display stats: {e}")

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def settings(self, ctx):
        """Show the current settings of the cog."""
        try:
            guild = ctx.guild
            moderation_threshold = await self.config.guild(guild).moderation_threshold()
            timeout_duration = await self.config.guild(guild).timeout_duration()
            log_channel_id = await self.config.guild(guild).log_channel()
            debug_mode = await self.config.guild(guild).debug_mode()
            whitelisted_channels = await self.config.guild(guild).whitelisted_channels()

            log_channel = guild.get_channel(log_channel_id) if log_channel_id else None
            log_channel_name = log_channel.mention if log_channel else "Not set"
            whitelisted_channels_names = ", ".join([guild.get_channel(ch_id).mention for ch_id in whitelisted_channels if guild.get_channel(ch_id)]) or "None"

            embed = discord.Embed(title="Current Omni Settings", color=discord.Color.green())
            embed.add_field(name="Moderation Threshold", value=str(moderation_threshold), inline=True)
            embed.add_field(name="Timeout Duration", value=f"{timeout_duration} minutes", inline=True)
            embed.add_field(name="Log Channel", value=log_channel_name, inline=True)
            embed.add_field(name="Debug Mode", value="Enabled" if debug_mode else "Disabled", inline=True)
            embed.add_field(name="Whitelisted Channels", value=whitelisted_channels_names, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to display settings: {e}")

    def cog_unload(self):
        try:
            if self.session and not self.session.closed:
                self.bot.loop.create_task(self.session.close())
        except Exception as e:
            raise RuntimeError(f"Failed to unload cog: {e}")

