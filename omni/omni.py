import discord
from redbot.core import commands, Config
import aiohttp
from datetime import timedelta
from collections import Counter
import unicodedata
import re

class Omni(commands.Cog):
    """AI-powered automatic text and image moderation provided by frontier moderation models"""

    VERSION = "0.0.1"

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
            cog_version=self.VERSION
        )
        self.session = aiohttp.ClientSession()
        self.message_count = 0
        self.moderated_count = 0
        self.moderated_users = set()
        self.category_counter = Counter()

    async def initialize(self):
        all_guilds = await self.config.all_guilds()
        for guild_id, data in all_guilds.items():
            self.message_count = data.get("message_count", 0)
            self.moderated_count = data.get("moderated_count", 0)
            self.moderated_users = set(data.get("moderated_users", []))
            self.category_counter = Counter(data.get("category_counter", {}))
            
            # Check for version update
            stored_version = data.get("cog_version", "0.0.0")
            if stored_version != self.VERSION:
                await self.notify_version_update(guild_id)
                await self.config.guild_from_id(guild_id).cog_version.set(self.VERSION)

    async def notify_version_update(self, guild_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        log_channel_id = await self.config.guild(guild).log_channel()
        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="AI moderation has been updated",
                    description=f"Your bot is now running version `{self.VERSION}`",
                    color=discord.Color.from_rgb(43, 189, 142)
                )
                await log_channel.send(embed=embed)

    def normalize_text(self, text):
        """Normalize text to replace with standard alphabetical/numeric characters."""
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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild = message.guild
        if not guild:
            return

        self.message_count += 1
        await self.config.guild(guild).message_count.set(self.message_count)

        api_tokens = await self.bot.get_shared_api_tokens("openai")
        api_key = api_tokens.get("api_key")
        if not api_key:
            return

        # Normalize the message content
        normalized_content = self.normalize_text(message.content)

        async with self.session.post(
            "https://api.openai.com/v1/moderations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={"input": normalized_content}
        ) as response:
            if response.status != 200:
                # Log the error if the request failed
                await self.log_message(message, {}, error_code=response.status)
                return

            data = await response.json()
            result = data.get("results", [{}])[0]
            flagged = result.get("flagged", False)
            category_scores = result.get("category_scores", {})

            if flagged:
                self.moderated_count += 1
                await self.config.guild(guild).moderated_count.set(self.moderated_count)
                self.moderated_users.add(message.author.id)
                await self.config.guild(guild).moderated_users.set(list(self.moderated_users))
                for category, score in category_scores.items():
                    if score > 0:
                        self.category_counter[category] += 1
                await self.config.guild(guild).category_counter.set(dict(self.category_counter))
                await self.handle_moderation(message, category_scores)

            # Check if debug mode is enabled
            debug_mode = await self.config.guild(guild).debug_mode()
            if debug_mode:
                await self.log_message(message, category_scores)

    async def handle_moderation(self, message, category_scores):
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
                    description=f"Message by {message.author.mention} was flagged and deleted.",
                    color=0xff4545
                )
                embed.add_field(name="Content", value=message.content, inline=False)
                moderation_threshold = await self.config.guild(guild).moderation_threshold()
                for category, score in category_scores.items():
                    if score == 0.00:
                        score_display = ":white_check_mark: Clean"
                    else:
                        score_display = f"**{score:.2f}**" if score > moderation_threshold else f"{score:.2f}"
                    embed.add_field(name=category.capitalize(), value=score_display, inline=True)
                await log_channel.send(embed=embed)

    async def log_message(self, message, category_scores, error_code=None):
        guild = message.guild
        log_channel_id = await self.config.guild(guild).log_channel()

        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="AI screened a message and found no threat",
                    description=f"Message by {message.author.mention} was logged.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Content", value=message.content, inline=False)
                moderation_threshold = await self.config.guild(guild).moderation_threshold()
                for category, score in category_scores.items():
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
                await owner.send(
                    f"Warning: No log channel is set for the guild '{guild.name}'. "
                    "Please set a log channel using the `[p]omni logs` command to enable message logging."
                )

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def omni(self, ctx):
        """AI-powered automatic text and image moderation provided by frontier moderation models"""
        pass

    @omni.command()
    async def threshold(self, ctx, threshold: float):
        """Set the moderation threshold (0 to 1)."""
        if 0 <= threshold <= 1:
            await self.config.guild(ctx.guild).moderation_threshold.set(threshold)
            await ctx.send(f"Moderation threshold set to {threshold}.")
        else:
            await ctx.send("Threshold must be between 0 and 1.")

    @omni.command()
    async def timeout(self, ctx, duration: int):
        """Set the timeout duration in minutes (0 for no timeout)."""
        if duration >= 0:
            await self.config.guild(ctx.guild).timeout_duration.set(duration)
            await ctx.send(f"Timeout duration set to {duration} minutes.")
        else:
            await ctx.send("Timeout duration must be 0 or greater.")

    @omni.command()
    async def logs(self, ctx, channel: discord.TextChannel):
        """Set the channel to log moderated messages."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}.")

    @omni.command()
    @commands.is_owner()
    async def debug(self, ctx):
        """Toggle debug mode to log all messages and their scores."""
        guild = ctx.guild
        current_debug_mode = await self.config.guild(guild).debug_mode()
        new_debug_mode = not current_debug_mode
        await self.config.guild(guild).debug_mode.set(new_debug_mode)
        status = "enabled" if new_debug_mode else "disabled"
        await ctx.send(f"Debug mode {status}.")

    @omni.command()
    async def stats(self, ctx):
        """Show statistics of the moderation activity."""
        top_categories = self.category_counter.most_common(5)
        top_categories_bullets = "\n".join([f"- {cat.capitalize()}: {count}" for cat, count in top_categories])
        
        embed = discord.Embed(title="✨ AI is hard at work for you", color=0xfffffe)
        embed.add_field(name="Messages processed", value=str(self.message_count), inline=True)
        embed.add_field(name="Messages moderated", value=str(self.moderated_count), inline=True)
        embed.add_field(name="Users punished", value=str(len(self.moderated_users)), inline=True)
        embed.add_field(name="Top violation categories", value=top_categories_bullets, inline=False)
        
        await ctx.send(embed=embed)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

