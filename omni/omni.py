import discord
from redbot.core import commands, Config
import aiohttp
from datetime import timedelta, datetime
from collections import Counter, defaultdict
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
            moderation_threshold=0.75,
            timeout_duration=0,
            log_channel=None,
            debug_mode=False,
            message_count=0,
            moderated_count=0,
            moderated_users=[],
            category_counter={},
            whitelisted_channels=[],
            cog_version=self.VERSION,
            moderation_enabled=True,
            user_message_counts={},
            image_count=0,
            moderated_image_count=0
        )
        self.config.register_global(
            global_message_count=0,
            global_moderated_count=0,
            global_moderated_users=[],
            global_category_counter={},
            global_image_count=0,
            global_moderated_image_count=0
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

            # Check if moderation is enabled
            moderation_enabled = await self.config.guild(guild).moderation_enabled()
            if not moderation_enabled:
                return

            # Check if the channel is whitelisted
            whitelisted_channels = await self.config.guild(guild).whitelisted_channels()
            if message.channel.id in whitelisted_channels:
                return

            # Update per-server and global statistics
            await self.increment_statistic(guild, 'message_count')
            await self.increment_statistic('global', 'global_message_count')

            # Update user message count
            await self.increment_user_message_count(guild, message.author.id)

            api_tokens = await self.bot.get_shared_api_tokens("openai")
            api_key = api_tokens.get("api_key")
            if not api_key:
                return

            # Ensure the session is open
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()

            # Normalize the message content
            normalized_content = self.normalize_text(message.content)

            # Prepare input for moderation API
            input_data = [{"type": "text", "text": normalized_content}]

            # Check for image attachments
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type.startswith("image/") and not attachment.content_type.endswith("gif"):
                        input_data.append({
                            "type": "image_url",
                            "image_url": {"url": attachment.url}
                        })
                        await self.increment_statistic(guild, 'image_count')
                        await self.increment_statistic('global', 'global_image_count')

            # Analyze text and image content
            text_category_scores = await self.analyze_content(input_data, api_key, message)

            # Determine if the message should be flagged based on the threshold
            moderation_threshold = await self.config.guild(guild).moderation_threshold()
            text_flagged = any(score > moderation_threshold for score in text_category_scores.values())

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
        if guild == 'global':
            current_value = await self.config.get_attr(stat_name)() + 1
            await self.config.get_attr(stat_name).set(current_value)
        else:
            current_value = await self.config.guild(guild).get_attr(stat_name)() + 1
            await self.config.guild(guild).get_attr(stat_name).set(current_value)

    async def increment_user_message_count(self, guild, user_id):
        user_message_counts = await self.config.guild(guild).user_message_counts()
        user_message_counts[user_id] = user_message_counts.get(user_id, 0) + 1
        await self.config.guild(guild).user_message_counts.set(user_message_counts)

    async def update_moderation_stats(self, guild, message, text_category_scores):
        await self.increment_statistic(guild, 'moderated_count')
        await self.increment_statistic('global', 'global_moderated_count')

        await self.update_user_list(guild, 'moderated_users', message.author.id)
        await self.update_user_list('global', 'global_moderated_users', message.author.id)

        await self.update_category_counter(guild, 'category_counter', text_category_scores)
        await self.update_category_counter('global', 'global_category_counter', text_category_scores)

        # Check if the message contains images and update moderated image count
        if any(attachment.content_type.startswith("image/") and not attachment.content_type.endswith("gif") for attachment in message.attachments):
            await self.increment_statistic(guild, 'moderated_image_count')
            await self.increment_statistic('global', 'global_moderated_image_count')

    async def update_user_list(self, guild, list_name, user_id):
        if guild == 'global':
            user_list = set(await self.config.get_attr(list_name)())
            user_list.add(user_id)
            await self.config.get_attr(list_name).set(list(user_list))
        else:
            user_list = set(await self.config.guild(guild).get_attr(list_name)())
            user_list.add(user_id)
            await self.config.guild(guild).get_attr(list_name).set(list(user_list))

    async def update_category_counter(self, guild, counter_name, text_category_scores):
        if guild == 'global':
            category_counter = Counter(await self.config.get_attr(counter_name)())
            for category, score in text_category_scores.items():
                if score > 0.2:
                    category_counter[category] += 1
            await self.config.get_attr(counter_name).set(dict(category_counter))
        else:
            category_counter = Counter(await self.config.guild(guild).get_attr(counter_name)())
            for category, score in text_category_scores.items():
                if score > 0.2:
                    category_counter[category] += 1
            await self.config.guild(guild).get_attr(counter_name).set(dict(category_counter))

    async def analyze_content(self, input_data, api_key, message):
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
                        "input": input_data
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("results", [{}])[0]
                        category_scores = result.get("category_scores", {})
                        return category_scores
                    elif response.status == 500:
                        await asyncio.sleep(5)  # Wait a few seconds before retrying
                    else:
                        # Log the error if the request failed
                        await self.log_message(message, {}, error_code=response.status)
                        return {}
        except Exception as e:
            raise RuntimeError(f"Failed to analyze content: {e}")

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
                        f"{category}: {score:.2f}" for category, score in category_scores.items() if score > 0.2
                    )
                    await message.author.timeout(timedelta(minutes=timeout_duration), reason=reason)
                except discord.Forbidden:
                    pass

            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="✨ Message moderated using AI",
                        description=f"The following message was deleted from chat because it may have violated the rules of the server, Discord's **[Terms of Service](<https://discord.com/terms>)**, or Discord's **[Community Guidelines](<https://discord.com/guidelines>)**...\n```{message.content}```",
                        color=0xff4545,
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Sent by", value=f"<@{message.author.id}> - `{message.author.id}`", inline=True)
                    embed.add_field(name="Sent in", value=f"<#{message.channel.id}> - `{message.channel.id}`", inline=True)
                    embed.add_field(name="Scoring", value=f"", inline=False)
                    moderation_threshold = await self.config.guild(guild).moderation_threshold()
                    sorted_scores = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]
                    for category, score in sorted_scores:
                        score_display = f"**{score:.2f}**" if score > moderation_threshold else f"{score:.2f}"
                        embed.add_field(name=category.capitalize(), value=score_display, inline=True)
                    
                    # Add image to embed if present
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.content_type.startswith("image/") and not attachment.content_type.endswith("gif"):
                                embed.set_image(url=attachment.url)
                                break

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
                    embed.add_field(name="Scoring", value=f"", inline=False)
                    moderation_threshold = await self.config.guild(guild).moderation_threshold()
                    sorted_scores = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]
                    for category, score in sorted_scores:
                        score_display = f"**{score:.2f}**" if score > moderation_threshold else f"{score:.2f}"
                        embed.add_field(name=category.capitalize(), value=score_display, inline=True)
                    if error_code:
                        embed.add_field(name="Error", value=f":x: `{error_code}` Failed to send to OpenAI endpoint.", inline=False)
                    
                    # Add image to embed if present
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.content_type.startswith("image/") and not attachment.content_type.endswith("gif"):
                                embed.set_image(url=attachment.url)
                                break

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
            image_count = await self.config.guild(ctx.guild).image_count()
            moderated_image_count = await self.config.guild(ctx.guild).moderated_image_count()

            member_count = ctx.guild.member_count
            moderated_message_percentage = (moderated_count / message_count * 100) if message_count > 0 else 0
            moderated_user_percentage = (len(moderated_users) / member_count * 100) if member_count > 0 else 0
            moderated_image_percentage = (moderated_image_count / image_count * 100) if image_count > 0 else 0

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
            embed.add_field(name=f"In {ctx.guild.name}", value="", inline=False)
            embed.add_field(name="Messages processed", value=f"**{message_count:,}** message{'s' if message_count != 1 else ''}", inline=True)
            embed.add_field(name="Messages moderated", value=f"**{moderated_count:,}** message{'s' if moderated_count != 1 else ''} ({moderated_message_percentage:.2f}%)", inline=True)
            embed.add_field(name="Users punished", value=f"**{len(moderated_users):,}** user{'s' if len(moderated_users) != 1 else ''} ({moderated_user_percentage:.2f}%)", inline=True)
            embed.add_field(name="Images processed", value=f"**{image_count:,}** image{'s' if image_count != 1 else ''}", inline=True)
            embed.add_field(name="Images moderated", value=f"**{moderated_image_count:,}** image{'s' if moderated_image_count != 1 else ''} ({moderated_image_percentage:.2f}%)", inline=True)
            embed.add_field(name="Estimated staff time saved", value=f"{time_saved_str} of **hands-on-keyboard** time", inline=False)
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
                embed.add_field(name="Trust and safety analysis", value=f"- **This server takes `{rank}{rank_suffix} place` out of `{total_guilds} servers`.**\n> In this scale, 1st place is the most abusive server, and your goal is to place as low as possible in position (losing is winning).\n\n- **This server is *statistically* more harmful than `{more_harmful_than_percentage:.2f}%` of servers, and less harmful than `{less_harmful_than_percentage:.2f}%` of servers.**\n> The goal is to be less harmful than as many servers as possible, as less harmful communities are most likely to foster more engagement and growth than their more abusive counterparts.\n\n- {moderation_rate_comparison}\n\n> The goal is to require as little moderation as possible and to be moderated under the global average.", inline=False)

                if rank in [1, 2, 3]:
                    embed.add_field(name="Discord compliance advisor", value="- :rotating_light: **Extreme risk**\n\n> This server needs **immediate** improvement in moderation and user behavior to avoid potential suspensions, terminations, or other assorted compliance measures.", inline=False)
                elif rank in range(4, 11):
                    embed.add_field(name="Discord compliance advisor", value="- :warning: **Approaching risk**\n\n> This server's not at immediate risk, but **improvement is needed** to keep it from getting to that point.", inline=False)
                else:
                    embed.add_field(name="Discord compliance advisor", value="- :white_check_mark: **Aim for continuing improvement**\n\n> This server's doing *comparatively* **OK**, but it's always best to be a safe, welcoming place to keep your server's safety ranking optimal.", inline=False)

                # Global statistics
                global_message_count = await self.config.global_message_count()
                global_moderated_count = await self.config.global_moderated_count()
                global_category_counter = Counter(await self.config.global_category_counter())
                global_image_count = await self.config.global_image_count()
                global_moderated_image_count = await self.config.global_moderated_image_count()

                global_moderated_message_percentage = (global_moderated_count / global_message_count * 100) if global_message_count > 0 else 0
                global_moderated_image_percentage = (global_moderated_image_count / global_image_count * 100) if global_image_count > 0 else 0

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
                embed.add_field(name="Across all monitored servers", value="", inline=False)
                embed.add_field(name="Messages processed", value=f"**{global_message_count:,}** message{'s' if global_message_count != 1 else ''}", inline=True)
                embed.add_field(name="Messages moderated", value=f"**{global_moderated_count:,}** message{'s' if global_moderated_count != 1 else ''} ({global_moderated_message_percentage:.2f}%)", inline=True)
                embed.add_field(name="Users punished", value=f"**{len(global_moderated_users):,}** user{'s' if len(global_moderated_users) != 1 else ''} ({global_moderated_user_percentage:.2f}%)", inline=True)
                embed.add_field(name="Images processed", value=f"**{global_image_count:,}** image{'s' if global_image_count != 1 else ''}", inline=True)
                embed.add_field(name="Images moderated", value=f"**{global_moderated_image_count:,}** image{'s' if global_moderated_image_count != 1 else ''} ({global_moderated_image_percentage:.2f}%)", inline=True)
                embed.add_field(name="Estimated staff time saved", value=f"{global_time_saved_str} of **hands-on-keyboard** time", inline=False)
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
            moderation_enabled = await self.config.guild(guild).moderation_enabled()

            log_channel = guild.get_channel(log_channel_id) if log_channel_id else None
            log_channel_name = log_channel.mention if log_channel else "Not set"
            whitelisted_channels_names = ", ".join([guild.get_channel(ch_id).mention for ch_id in whitelisted_channels if guild.get_channel(ch_id)]) or "None"

            embed = discord.Embed(title="Current Omni Settings", color=discord.Color.green())
            embed.add_field(name="Moderation Threshold", value=str(moderation_threshold), inline=True)
            embed.add_field(name="Timeout Duration", value=f"{timeout_duration} minutes", inline=True)
            embed.add_field(name="Log Channel", value=log_channel_name, inline=True)
            embed.add_field(name="Debug Mode", value="Enabled" if debug_mode else "Disabled", inline=True)
            embed.add_field(name="Whitelisted Channels", value=whitelisted_channels_names, inline=False)
            embed.add_field(name="Moderation Enabled", value="Yes" if moderation_enabled else "No", inline=True)

            await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to display settings: {e}")

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def toggle(self, ctx):
        """Toggle automatic moderation on or off."""
        try:
            guild = ctx.guild
            current_status = await self.config.guild(guild).moderation_enabled()
            new_status = not current_status
            await self.config.guild(guild).moderation_enabled.set(new_status)
            status = "enabled" if new_status else "disabled"
            await ctx.send(f"Automatic moderation {status}.")
        except Exception as e:
            raise RuntimeError(f"Failed to toggle automatic moderation: {e}")

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

    @omni.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def users(self, ctx):
        """Show the 5 most and least frequently moderated users."""
        try:
            guild = ctx.guild
            user_message_counts = await self.config.guild(guild).user_message_counts()
            moderated_users = await self.config.guild(guild).moderated_users()
            user_image_counts = await self.config.guild(guild).image_count()
            moderated_image_counts = await self.config.guild(guild).moderated_image_count()

            # Calculate moderation percentages
            user_moderation_percentages = {
                user_id: (user_message_counts.get(user_id, 0), moderated_users.count(user_id))
                for user_id in user_message_counts
            }

            # Sort users by moderation percentage
            most_moderated = sorted(user_moderation_percentages.items(), key=lambda x: x[1][1] / x[1][0] if x[1][0] > 0 else 0, reverse=True)[:5]
            least_moderated = sorted(user_moderation_percentages.items(), key=lambda x: x[1][1] / x[1][0] if x[1][0] > 0 else 0)[:5]

            embed = discord.Embed(title=f"{ctx.guild.name}'s most/least moderated members", color=0xfffffe)

            # Add fields for most moderated users
            for user_id, (total, moderated) in most_moderated:
                if total > 0:
                    user = await self.bot.fetch_user(user_id)
                    embed.add_field(
                        name=f"{user.name} (ID: {user_id})",
                        value=f"📝 **{total}**\n🚨 **{moderated}** ({(moderated / total * 100):.2f}%)\n🖼️ **{user_image_counts}**\n🚨🖼️ **{moderated_image_counts}**",
                        inline=False
                    )

            # Add fields for least moderated users
            for user_id, (total, moderated) in least_moderated:
                if total > 0:
                    user = await self.bot.fetch_user(user_id)
                    embed.add_field(
                        name=f"{user.name} (ID: {user_id})",
                        value=f"📝 **{total}**\n🚨 **{moderated}** ({(moderated / total * 100):.2f}%)\n🖼️ **{user_image_counts}**\n🚨🖼️ **{moderated_image_counts}**",
                        inline=False
                    )

            await ctx.send(embed=embed)
        except Exception as e:
            raise RuntimeError(f"Failed to display user moderation statistics: {e}")

    @omni.command()
    @commands.is_owner()
    async def cleanup(self, ctx):
        """Reset all server and global statistics and counters."""
        try:
            # Warning message
            warning_embed = discord.Embed(
                title="Warning",
                description="This operation is computationally intensive and will reset all server and global statistics and counters. Please confirm by typing 'CONFIRM'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=warning_embed)

            def check(m):
                return m.author == ctx.author and m.content == "CONFIRM" and m.channel == ctx.channel

            try:
                await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("Cleanup operation cancelled due to timeout.")
                return

            # Calculate data size before cleanup
            total_data_size = 0
            all_guilds = await self.config.all_guilds()
            for guild_id, data in all_guilds.items():
                total_data_size += sum(len(str(value)) for value in data.values())

            global_data = await self.config.all_global()
            total_data_size += sum(len(str(value)) for value in global_data.values())

            # Reset all guild statistics
            for guild_id in all_guilds:
                guild_conf = self.config.guild_from_id(guild_id)
                await guild_conf.message_count.set(0)
                await guild_conf.moderated_count.set(0)
                await guild_conf.moderated_users.set([])
                await guild_conf.category_counter.set({})
                await guild_conf.user_message_counts.set({})
                await guild_conf.image_count.set(0)
                await guild_conf.moderated_image_count.set(0)

            # Reset global statistics
            await self.config.global_message_count.set(0)
            await self.config.global_moderated_count.set(0)
            await self.config.global_moderated_users.set([])
            await self.config.global_category_counter.set({})
            await self.config.global_image_count.set(0)
            await self.config.global_moderated_image_count.set(0)

            # Calculate data size after cleanup
            data_size_after_cleanup = 0
            all_guilds = await self.config.all_guilds()
            for guild_id, data in all_guilds.items():
                data_size_after_cleanup += sum(len(str(value)) for value in data.values())

            global_data = await self.config.all_global()
            data_size_after_cleanup += sum(len(str(value)) for value in global_data.values())

            # Calculate deleted data size
            deleted_data_size = total_data_size - data_size_after_cleanup

            # Convert to appropriate size unit
            if deleted_data_size < 1024:
                size_str = f"{deleted_data_size} bytes"
            elif deleted_data_size < 1024**2:
                size_str = f"{deleted_data_size / 1024:.2f} KB"
            else:
                size_str = f"{deleted_data_size / 1024**2:.2f} MB"

            # Confirmation message
            confirmation_embed = discord.Embed(
                title="Cleanup Complete",
                description=f"All statistics and counters have been reset.\nTotal data deleted: {size_str}.",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirmation_embed)

        except Exception as e:
            raise RuntimeError(f"Failed to reset statistics: {e}")

    def cog_unload(self):
        try:
            if self.session and not self.session.closed:
                self.bot.loop.create_task(self.session.close())
        except Exception as e:
            raise RuntimeError(f"Failed to unload cog: {e}")

