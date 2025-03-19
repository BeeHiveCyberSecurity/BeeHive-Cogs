import discord
from redbot.core import commands, Config
import aiohttp
from datetime import timedelta, datetime
from collections import Counter
import unicodedata
import re
import asyncio

class Omni(commands.Cog):
    """AI-powered automatic text moderation provided by frontier moderation models"""

    VERSION = "0.0.3"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(
            moderation_threshold=0.70,
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
        self.config.register_global(
            global_message_count=0,
            global_moderated_count=0,
            global_moderated_users=[],
            global_category_counter={}
        )
        self.session = None

    async def initialize(self):
        try:
            self.session = aiohttp.ClientSession()
            all_guilds = await self.config.all_guilds()
            for guild_id, data in all_guilds.items():
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
            replacements = {'nègre': 'negro', 'reggin': 'nigger'}
            for word, replacement in replacements.items():
                text = text.replace(word, replacement)
            # Replace multiple spaces with a single space
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            raise ValueError(f"Failed to normalize text: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.process_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.process_message(after)

    async def process_message(self, message):
        try:
            if message.author.bot or not message.guild:
                return

            guild = message.guild

            # Check if the channel is whitelisted
            whitelisted_channels = await self.config.guild(guild).whitelisted_channels()
            if message.channel.id in whitelisted_channels:
                return

            # Update per-server and global statistics
            await self.increment_statistic(guild, 'message_count')
            await self.increment_statistic(None, 'global_message_count')

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
                await self.update_moderation_stats(guild, message, text_category_scores)
                await self.handle_moderation(message, text_category_scores)

            # Check if debug mode is enabled
            debug_mode = await self.config.guild(guild).debug_mode()
            if debug_mode:
                await self.log_message(message, text_category_scores)
        except Exception as e:
            raise RuntimeError(f"Error processing message: {e}")

    async def increment_statistic(self, guild, stat_name):
        if guild:
            current_value = await self.config.guild(guild).get_attr(stat_name)() + 1
            await self.config.guild(guild).get_attr(stat_name).set(current_value)
        else:
            current_value = await self.config.get_attr(stat_name)() + 1
            await self.config.get_attr(stat_name).set(current_value)

    async def update_moderation_stats(self, guild, message, text_category_scores):
        await self.increment_statistic(guild, 'moderated_count')
        await self.increment_statistic(None, 'global_moderated_count')

        await self.update_user_list(guild, 'moderated_users', message.author.id)
        await self.update_user_list(None, 'global_moderated_users', message.author.id)

        await self.update_category_counter(guild, 'category_counter', text_category_scores)
        await self.update_category_counter(None, 'global_category_counter', text_category_scores)

    async def update_user_list(self, guild, list_name, user_id):
        user_list = set(await self.config.guild(guild).get_attr(list_name)())
        user_list.add(user_id)
        await self.config.guild(guild).get_attr(list_name).set(list(user_list))

    async def update_category_counter(self, guild, counter_name, text_category_scores):
        category_counter = Counter(await self.config.guild(guild).get_attr(counter_name)())
        for category, score in text_category_scores.items():
            if score > 0:
                category_counter[category] += 1
        await self.config.guild(guild).get_attr(counter_name).set(dict(category_counter))

    async def analyze_text(self, text, api_key, message):
        try:
            while True:
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
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("results", [{}])[0]
                        flagged = result.get("flagged", False)
                        category_scores = result.get("category_scores", {})
                        return flagged, category_scores
                    elif response.status == 500:
                        await asyncio.sleep(5)  # Wait a few seconds before retrying
                    else:
                        # Log the error if the request failed
                        await self.log_message(message, {}, error_code=response.status)
                        return False, {}
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
                # Add user to moderated users list if message is deleted
                await self.update_user_list(guild, 'moderated_users', message.author.id)
            except discord.NotFound:
                pass  

            if timeout_duration > 0:
                try:
                    reason = "AI moderator action. Violation scores: " + ", ".join(
                        f"{category}: {score:.2f}" for category, score in category_scores.items() if score > 0
                    )
                    await message.author.timeout(timedelta(minutes=timeout_duration), reason=reason)
                except discord.Forbidden:
                    pass

            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="✨ Message moderated using AI",
                        description=f"The following message was deleted from chat because it may have violated the rules of the server, Discord's Terms of Service, or Discord's Community Guidelines..\n```{message.content}```",
                        color=0xff4545,
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Sent by", value=f"<@{message.author.id}> - `{message.author.id}`", inline=True)
                    embed.add_field(name="Sent in", value=f"<#{message.channel.id}> - `{message.channel.id}`", inline=True)
                    embed.add_field(name="Violation scores", value=f"", inline=False)
                    moderation_threshold = await self.config.guild(guild).moderation_threshold()
                    sorted_scores = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]
                    for category, score in sorted_scores:
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
                        title="✨ Message processed using AI",
                        description=f"The following message was processed\n```{message.content}```",
                        color=0xfffffe,
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Sent by", value=f"<@{message.author.id}> - `{message.author.id}`", inline=True)
                    embed.add_field(name="Sent in", value=f"<#{message.channel.id}> - `{message.channel.id}`", inline=True)
                    embed.add_field(name="Violation scores", value=f"", inline=False)
                    moderation_threshold = await self.config.guild(guild).moderation_threshold()
                    sorted_scores = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]
                    for category, score in sorted_scores:
                        score_display = f"**{score:.2f}**" if score > moderation_threshold else f"{score:.2f}"
                        embed.add_field(name=category.capitalize(), value=score_display, inline=True)
                    if error_code:
                        embed.add_field(name="Error", value=f":x: `{error_code}` Failed to send to OpenAI endpoint.", inline=False)
                    await log_channel.send(embed=embed)
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
            # Local statistics
            message_count = await self.config.guild(ctx.guild).message_count()
            moderated_count = await self.config.guild(ctx.guild).moderated_count()
            moderated_users = await self.config.guild(ctx.guild).moderated_users()
            category_counter = Counter(await self.config.guild(ctx.guild).category_counter())

            member_count = ctx.guild.member_count
            moderated_message_percentage = (moderated_count / message_count * 100) if message_count > 0 else 0
            moderated_user_percentage = (len(moderated_users) / member_count * 100) if member_count > 0 else 0

            # Calculate estimated moderator time saved
            time_saved_seconds = (moderated_count * 5) + message_count  # 5 seconds per moderated message + 1 second per message read
            time_saved_minutes, time_saved_seconds = divmod(time_saved_seconds, 60)
            time_saved_hours, time_saved_minutes = divmod(time_saved_minutes, 60)
            time_saved_days, time_saved_hours = divmod(time_saved_hours, 24)

            if time_saved_days > 0:
                time_saved_str = f"**{time_saved_days}** day{'s' if time_saved_days != 1 else ''}, **{time_saved_hours}** hour{'s' if time_saved_hours != 1 else ''}"
            elif time_saved_hours > 0:
                time_saved_str = f"**{time_saved_hours}** hour{'s' if time_saved_hours != 1 else ''}, **{time_saved_minutes}** minute{'s' if time_saved_minutes != 1 else ''}"
            elif time_saved_minutes > 0:
                time_saved_str = f"**{time_saved_minutes}** minute{'s' if time_saved_minutes != 1 else ''}, **{time_saved_seconds}** second{'s' if time_saved_seconds != 1 else ''}"
            else:
                time_saved_str = f"**{time_saved_seconds}** second{'s' if time_saved_seconds != 1 else ''}"

            top_categories = category_counter.most_common(5)
            top_categories_bullets = "\n".join([f"- **{cat.capitalize()}** x{count:,}" for cat, count in top_categories])
            
            embed = discord.Embed(title="✨ AI is hard at work for you, here's everything Omni knows...", color=0xfffffe)
            embed.add_field(name="In this server", value="", inline=False)
            embed.add_field(name="Messages processed", value=f"**{message_count:,}** message{'s' if message_count != 1 else ''}", inline=True)
            embed.add_field(name="Messages moderated", value=f"**{moderated_count:,}** message{'s' if moderated_count != 1 else ''} ({moderated_message_percentage:.2f}%)", inline=True)
            embed.add_field(name="Users punished", value=f"**{len(moderated_users):,}** user{'s' if len(moderated_users) != 1 else ''} ({moderated_user_percentage:.2f}%)", inline=True)
            embed.add_field(name="Estimated staff time saved", value=f"{time_saved_str} hands-on-keyboard time", inline=False)
            embed.add_field(name="Most frequent flags", value=top_categories_bullets, inline=False)

            # Show global stats, trust and safety analysis, and discord compliance if in more than 45 servers
            if len(self.bot.guilds) > 45:
                # Calculate guilds sorted by harmfulness
                guilds_sorted_by_harmfulness = await self._get_guilds_sorted_by_harmfulness()
                rank = guilds_sorted_by_harmfulness.index(ctx.guild) + 1
                total_guilds = len(guilds_sorted_by_harmfulness)
                more_harmful_than_percentage = ((total_guilds - rank) / total_guilds) * 100
                less_harmful_than_percentage = (rank / total_guilds) * 100

                # Calculate member moderation rate comparison
                global_moderated_users = await self.config.global_moderated_users()
                total_members = sum(guild.member_count for guild in self.bot.guilds)
                global_moderated_user_percentage = (len(global_moderated_users) / total_members * 100) if total_members > 0 else 0
                moderation_rate_difference = moderated_user_percentage - global_moderated_user_percentage
                if moderation_rate_difference > 0:
                    moderation_rate_comparison = f"**Members in this server require `{moderation_rate_difference:.2f}%` more moderation on average compared to the global average.**\n> *This server may have more abrasive users than most other servers in statistical comparison.*"
                elif moderation_rate_difference < 0:
                    moderation_rate_comparison = f"**Members in this server require `{-moderation_rate_difference:.2f}%` less moderation on average compared to the global average.**\n> *This server has members that are statistically friendlier and require less moderation & guidance.*"
                else:
                    moderation_rate_comparison = "**Members in this server require the same level of moderation on average compared to the global average.**\n> *Standard internet users, to statistical expectation.*"

                def get_ordinal_suffix(n):
                    if 10 <= n % 100 <= 20:
                        suffix = 'th'
                    else:
                        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
                    return suffix

                rank_suffix = get_ordinal_suffix(rank)
                embed.add_field(name="Trust and safety analysis", value=f"- **This server takes `{rank}{rank_suffix} place` out of `{total_guilds} servers`.**\n> In this scale, 1st place is the most abusive server, and your goal is to place as low as possible in position (losing is winning).\n\n- **This server is *statistically* more harmful than `{more_harmful_than_percentage:.2f}%` of servers, and less harmful than `{less_harmful_than_percentage:.2f}%` of servers.**\n> The goal is to be less harmful than as many server as possible, as less harmful communities are most likely to foster more engagement and growth than their more abusive counterparts.\n\n- {moderation_rate_comparison}\n\n> The goal is to require as little moderation as possible and to be moderated under the global average.", inline=False)

                if rank in [1, 2, 3]:
                    embed.add_field(name="Discord compliance advisor", value=":rotating_light: **Extreme risk**\n> This server needs immediate improvement in moderation and user behavior to avoid potential suspensions, terminations, or other assorted compliance measures.", inline=False)
                elif rank in range(4, 11):
                    embed.add_field(name="Discord compliance advisor", value=":warning: **Approaching risk**\n> This server's not at immediate risk, but improvement is needed to keep it from getting to that point.", inline=False)
                else:
                    embed.add_field(name="Discord compliance advisor", value=":white_check_mark: **Aim for continuing improvement**\n> This server's doing comparatively OK, but it's always best to be a safe, welcoming place to keep your server's safety ranking optimal.", inline=False)

                # Global statistics
                global_message_count = await self.config.global_message_count()
                global_moderated_count = await self.config.global_moderated_count()
                global_category_counter = Counter(await self.config.global_category_counter())

                global_moderated_message_percentage = (global_moderated_count / global_message_count * 100) if global_message_count > 0 else 0

                # Calculate global estimated moderator time saved
                global_time_saved_seconds = (global_moderated_count * 5) + global_message_count  # 5 seconds per moderated message + 1 second per message read
                global_time_saved_minutes, global_time_saved_seconds = divmod(global_time_saved_seconds, 60)
                global_time_saved_hours, global_time_saved_minutes = divmod(global_time_saved_minutes, 60)
                global_time_saved_days, global_time_saved_hours = divmod(global_time_saved_hours, 24)

                if global_time_saved_days > 0:
                    global_time_saved_str = f"**{global_time_saved_days}** day{'s' if global_time_saved_days != 1 else ''}, **{global_time_saved_hours}** hour{'s' if global_time_saved_hours != 1 else ''}"
                elif global_time_saved_hours > 0:
                    global_time_saved_str = f"**{global_time_saved_hours}** hour{'s' if global_time_saved_hours != 1 else ''}, **{global_time_saved_minutes}** minute{'s' if global_time_saved_minutes != 1 else ''}"
                elif global_time_saved_minutes > 0:
                    global_time_saved_str = f"**{global_time_saved_minutes}** minute{'s' if global_time_saved_minutes != 1 else ''}, **{global_time_saved_seconds}** second{'s' if global_time_saved_seconds != 1 else ''}"
                else:
                    global_time_saved_str = f"**{global_time_saved_seconds}** second{'s' if global_time_saved_seconds != 1 else ''}"

                global_top_categories = global_category_counter.most_common(5)
                global_top_categories_bullets = "\n".join([f"- **{cat.capitalize()}** x{count:,}" for cat, count in global_top_categories])
                embed.add_field(name="Across all servers", value="", inline=False)
                embed.add_field(name="Messages processed", value=f"**{global_message_count:,}** message{'s' if global_message_count != 1 else ''}", inline=True)
                embed.add_field(name="Messages moderated", value=f"**{global_moderated_count:,}** message{'s' if global_moderated_count != 1 else ''} ({global_moderated_message_percentage:.2f}%)", inline=True)
                embed.add_field(name="Users punished", value=f"**{len(global_moderated_users):,}** user{'s' if len(global_moderated_users) != 1 else ''} ({global_moderated_user_percentage:.2f}%)", inline=True)
                embed.add_field(name="Estimated staff time saved", value=f"{global_time_saved_str} hands-on-keyboard time", inline=False)
                embed.add_field(name="Most frequent flags", value=global_top_categories_bullets, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to display stats: {e}")

    async def _get_guilds_sorted_by_harmfulness(self):
        """Helper function to sort guilds by harmfulness."""
        guilds_with_harmfulness = []
        for guild in self.bot.guilds:
            message_count = await self.config.guild(guild).message_count() or 1
            moderated_count = await self.config.guild(guild).moderated_count()
            harmfulness = moderated_count / message_count
            guilds_with_harmfulness.append((guild, harmfulness))
        guilds_sorted_by_harmfulness = sorted(guilds_with_harmfulness, key=lambda x: x[1], reverse=True)
        return [guild for guild, _ in guilds_sorted_by_harmfulness]

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

    @omni.command()
    async def reasons(self, ctx):
        """Explains how the AI moderator labels and categorizes content"""
        try:
            categories = {
                "harassment": "Content that expresses, incites, or promotes harassing language towards any target.",
                "harassment/threatening": "Harassment content that also includes violence or serious harm towards any target.",
                "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
                "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
                "illicit": "Content that gives advice or instruction on how to commit illicit acts.",
                "illicit/violent": "The same types of content flagged by the illicit category, but also includes references to violence or procuring a weapon.",
                "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
                "self-harm/intent": "Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm.",
                "self-harm/instructions": "Content that encourages performing acts of self-harm or that gives instructions or advice on how to commit such acts.",
                "sexual": "Content meant to arouse sexual excitement or that promotes sexual services.",
                "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
                "violence": "Content that depicts death, violence, or physical injury.",
                "violence/graphic": "Content that depicts death, violence, or physical injury in graphic detail."
            }

            embed = discord.Embed(title="What the AI moderator is looking for", color=0xfffffe)
            for category, description in categories.items():
                embed.add_field(name=category.capitalize(), value=description, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to display reasons: {e}")

    def cog_unload(self):
        try:
            if self.session and not self.session.closed:
                self.bot.loop.create_task(self.session.close())
        except Exception as e:
            raise RuntimeError(f"Failed to unload cog: {e}")

