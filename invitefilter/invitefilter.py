import discord
from redbot.core import commands, Config # type: ignore
import re
import datetime  # Added for timedelta

class InviteFilter(commands.Cog):
    """A cog to detect and remove Discord server invites from chat."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=22222222222)
        self._register_config()

    def _register_config(self):
        """Register configuration defaults."""
        self.config.register_guild(
            delete_invites=True,
            whitelisted_channels=[],
            whitelisted_roles=[],
            logging_channel=None,
            timeout_duration=1,  # Default to 1 minute timeout
            invites_deleted=0,
            timeouts_issued=0, # Track number of timeouts
            total_timeout_minutes=0 # Track total minutes applied
        )
        self.config.register_global(
            total_invites_deleted=0
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        guild = message.guild
        member = message.author # Use member object for timeout

        # Check if filtering is enabled
        if not await self.config.guild(guild).delete_invites():
            return

        # Check channel whitelist
        if message.channel.id in await self.config.guild(guild).whitelisted_channels():
            return

        # Check role whitelist (ensure member object is used)
        if isinstance(member, discord.Member): # Ensure it's a member object before checking roles
            whitelisted_roles = await self.config.guild(guild).whitelisted_roles()
            # Use member.roles directly
            if any(role.id in whitelisted_roles for role in member.roles):
                return
        else:
             # This case should ideally not happen in guilds, but safety check
             return


        # Enhanced invite pattern to catch variations like ".gg/server"
        # Regex needs to capture the code part for fetch_invite if the full URL isn't present
        # Using a more robust regex to capture various forms and extract the code
        invite_pattern = r"(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite|dsc\.gg|invite\.gg)[/](?P<code>[a-zA-Z0-9\-]+)"
        full_url_pattern = r"(?:https?://)?(?:www\.)?" + invite_pattern # For logging the full match

        match = re.search(invite_pattern, message.content, re.IGNORECASE)
        full_match = re.search(full_url_pattern, message.content, re.IGNORECASE)

        if match:
            invite_code = match.group("code")
            log_invite_url = full_match.group(0) if full_match else f"discord.gg/{invite_code}" # Log the matched URL or construct one

            actions_taken = []
            log_fields = {}
            invite_info = None # Store invite info for logging

            # Fetch invite details first (if possible) to log them even if deletion/timeout fails
            try:
                # Use the extracted code which is more reliable for fetch_invite
                invite_info = await self.bot.fetch_invite(invite_code)
                log_fields["Server name"] = invite_info.guild.name if invite_info.guild else "Unknown (Group DM or Deleted Server)"
                log_fields["Server ID"] = invite_info.guild.id if invite_info.guild else "N/A"
                log_fields["Member count"] = getattr(invite_info, 'approximate_member_count', 'N/A') # Use getattr for safety
                log_fields["Online now"] = getattr(invite_info, 'approximate_presence_count', 'N/A')
            except discord.NotFound:
                log_fields["Invite Status"] = "Invalid or Expired"
            except discord.HTTPException as e:
                log_fields["Invite Fetch Error"] = f"HTTP Error: {e.status}"
            # No except discord.Forbidden here, handle below for specific actions

            # --- Action: Delete Message ---
            try:
                await message.delete()
                actions_taken.append("Message deleted")
                # Increment counters only on successful deletion
                current_guild_deleted = await self.config.guild(guild).invites_deleted()
                await self.config.guild(guild).invites_deleted.set(current_guild_deleted + 1)
                current_total_deleted = await self.config.total_invites_deleted()
                await self.config.total_invites_deleted.set(current_total_deleted + 1)
            except discord.Forbidden:
                actions_taken.append("Deletion failed (Missing Permissions)")
            except discord.NotFound:
                actions_taken.append("Deletion failed (Message already deleted)")
            except discord.HTTPException as e:
                 actions_taken.append(f"Deletion failed (HTTP Error: {e.status})")


            # --- Action: Timeout User ---
            timeout_duration_minutes = await self.config.guild(guild).timeout_duration()
            if timeout_duration_minutes > 0 and isinstance(member, discord.Member): # Check if timeout is enabled and we have a member object
                # Ensure the bot has permissions higher than the target user
                if guild.me.top_role > member.top_role:
                    timeout_delta = datetime.timedelta(minutes=timeout_duration_minutes)
                    try:
                        await member.timeout(timeout_delta, reason="Sent Discord invite link")
                        actions_taken.append(f"Timeout issued for {timeout_duration_minutes} minutes")
                        # Increment timeout stats on success
                        current_timeouts = await self.config.guild(guild).timeouts_issued()
                        await self.config.guild(guild).timeouts_issued.set(current_timeouts + 1)
                        current_total_minutes = await self.config.guild(guild).total_timeout_minutes()
                        await self.config.guild(guild).total_timeout_minutes.set(current_total_minutes + timeout_duration_minutes)
                    except discord.Forbidden:
                        actions_taken.append(f"Timeout failed (Missing Permissions or Role Hierarchy)")
                    except discord.HTTPException as e:
                        actions_taken.append(f"Timeout failed (HTTP Error: {e.status})")
                else:
                    actions_taken.append(f"Timeout skipped (Bot role not high enough)")


            # --- Action: Log Event ---
            logging_channel_id = await self.config.guild(guild).logging_channel()
            if logging_channel_id:
                logging_channel = guild.get_channel(logging_channel_id)
                if logging_channel and logging_channel.permissions_for(guild.me).send_messages and logging_channel.permissions_for(guild.me).embed_links:
                    embed = discord.Embed(
                        title="💬 Invite Filter Action",
                        description="An invite link was detected and processed.",
                        color=discord.Color.red() # Use discord Color object
                    )
                    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
                    embed.add_field(name="Detected Invite", value=f"`{log_invite_url}`", inline=False) # Use the matched URL

                    # Add invite details if fetched
                    for name, value in log_fields.items():
                         embed.add_field(name=name, value=value, inline=True)

                    if actions_taken:
                        embed.add_field(name="Actions Taken", value="\n".join(f"- {action}" for action in actions_taken), inline=False)
                    else:
                         embed.add_field(name="Actions Taken", value="None", inline=False)

                    embed.set_footer(text=f"Message ID: {message.id}")
                    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

                    try:
                        await logging_channel.send(embed=embed)
                    except discord.HTTPException:
                        # Log failure to send log message (e.g., to console or another fallback)
                        print(f"Failed to send invite filter log to channel {logging_channel_id} in guild {guild.id}")
                elif logging_channel:
                     print(f"Missing Send/Embed permissions for invite filter log channel {logging_channel_id} in guild {guild.id}")


    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(invoke_without_command=True, aliases=["if"])
    async def invitefilter(self, ctx):
        """Manage the invite filter settings."""
        await ctx.send_help(ctx.command)

    @invitefilter.command()
    async def toggle(self, ctx, on_off: bool = None):
        """Toggle the invite filter on or off.

        If `on_off` is not provided, the current state will be flipped.
        Provide `True` to enable or `False` to disable.
        """
        guild = ctx.guild
        current_status = await self.config.guild(guild).delete_invites()
        if on_off is None:
            new_status = not current_status
        else:
            new_status = on_off

        await self.config.guild(guild).delete_invites.set(new_status)
        status = "enabled" if new_status else "disabled"
        await ctx.send(f"✅ Invite filter is now **{status}**.")

    @invitefilter.group(invoke_without_command=True)
    async def whitelist(self, ctx):
        """Manage the invite filter whitelist (channels and roles)."""
        await ctx.send_help(ctx.command)

    @whitelist.command(name="channel")
    async def whitelist_channel(self, ctx, channel: discord.TextChannel):
        """Add or remove a channel from the invite filter whitelist."""
        guild = ctx.guild
        # Use context manager for safe list modification
        async with self.config.guild(guild).whitelisted_channels() as whitelisted_channels:
            changelog = []
            if channel.id in whitelisted_channels:
                try:
                    whitelisted_channels.remove(channel.id)
                    changelog.append(f"➖ Removed channel: {channel.mention}")
                except ValueError:
                     # Should not happen with the 'in' check, but safety first
                     await ctx.send("Error removing channel, it might have already been removed.")
                     return
            else:
                whitelisted_channels.append(channel.id)
                changelog.append(f"➕ Added channel: {channel.mention}")

        if changelog:
            changelog_message = "\n".join(changelog)
            embed = discord.Embed(title="Whitelist Channel Updated", description=changelog_message, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
             await ctx.send("No changes made to the channel whitelist.") # Should not happen based on logic, but good practice

    @whitelist.command(name="role")
    async def whitelist_role(self, ctx, role: discord.Role):
        """Add or remove a role from the invite filter whitelist."""
        guild = ctx.guild
        # Use context manager for safe list modification
        async with self.config.guild(guild).whitelisted_roles() as whitelisted_roles:
            changelog = []
            if role.id in whitelisted_roles:
                try:
                    whitelisted_roles.remove(role.id)
                    changelog.append(f"➖ Removed role: {role.mention}") # Use mention for roles too
                except ValueError:
                    await ctx.send("Error removing role, it might have already been removed.")
                    return
            else:
                whitelisted_roles.append(role.id)
                changelog.append(f"➕ Added role: {role.mention}")

        if changelog:
            changelog_message = "\n".join(changelog)
            embed = discord.Embed(title="Whitelist Role Updated", description=changelog_message, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send("No changes made to the role whitelist.")

    @invitefilter.command(name="logchannel", aliases=["logs"])
    async def set_log_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the logging channel for invite detections.

        Provide no channel to disable logging.
        """
        guild = ctx.guild
        if channel:
            # Check bot permissions in the target channel
            if not channel.permissions_for(guild.me).send_messages or not channel.permissions_for(guild.me).embed_links:
                 await ctx.send(f"⚠️ I lack `Send Messages` or `Embed Links` permissions in {channel.mention}. Please grant them for logging to work.")
                 return
            await self.config.guild(guild).logging_channel.set(channel.id)
            await ctx.send(f"✅ Logging channel set to {channel.mention}.")
        else:
            await self.config.guild(guild).logging_channel.set(None)
            await ctx.send("✅ Logging channel disabled.")


    @invitefilter.command(aliases=["duration"])
    async def timeout(self, ctx, minutes: int):
        """Set the timeout duration in minutes when an invite is detected.

        Set to 0 to disable timeouts. Maximum is 40320 minutes (28 days).
        """
        guild = ctx.guild
        # Discord timeout limit is 28 days (28 * 24 * 60 = 40320 minutes)
        if not 0 <= minutes <= 40320:
             await ctx.send("⚠️ Timeout duration must be between 0 and 40320 minutes (28 days).")
             return

        await self.config.guild(guild).timeout_duration.set(minutes)
        if minutes > 0:
            await ctx.send(f"✅ Timeout duration set to **{minutes}** minutes.")
        else:
            await ctx.send("✅ Timeouts for invite detection are now **disabled**.")

    @invitefilter.command()
    async def stats(self, ctx):
        """Display statistics for the invite filter."""
        guild = ctx.guild
        invites_deleted = await self.config.guild(guild).invites_deleted()
        timeouts_issued = await self.config.guild(guild).timeouts_issued()
        total_timeout_minutes = await self.config.guild(guild).total_timeout_minutes()
        timeout_duration = await self.config.guild(guild).timeout_duration() # Current setting
        total_invites_deleted = await self.config.total_invites_deleted()

        embed = discord.Embed(title="📊 Invite Filter Stats", color=discord.Color.blurple()) # Use standard color

        # Guild Stats
        guild_stats = [
            f"**Invites Deleted:** {invites_deleted}",
            f"**Timeouts Issued:** {timeouts_issued}",
            f"**Total Timeout Minutes Applied:** {total_timeout_minutes}",
            f"**Current Timeout Setting:** {timeout_duration} minutes" + (" (disabled)" if timeout_duration == 0 else "")
        ]
        embed.add_field(name=f"In {guild.name}", value="\n".join(guild_stats), inline=False)

        # Global Stats
        embed.add_field(name="Across All Servers", value=f"**Total Invites Deleted:** {total_invites_deleted}", inline=False)

        await ctx.send(embed=embed)

    @invitefilter.command()
    async def settings(self, ctx):
        """Display the current settings of the invite filter."""
        guild = ctx.guild
        config_data = await self.config.guild(guild).all()

        delete_invites = config_data['delete_invites']
        whitelisted_channels_ids = config_data['whitelisted_channels']
        whitelisted_roles_ids = config_data['whitelisted_roles']
        logging_channel_id = config_data['logging_channel']
        timeout_duration = config_data['timeout_duration']

        # Fetch mentions/names safely
        whitelisted_channels_mentions = [c.mention for i in whitelisted_channels_ids if (c := guild.get_channel(i))]
        whitelisted_roles_mentions = [r.mention for i in whitelisted_roles_ids if (r := guild.get_role(i))] # Use mention for roles
        logging_channel_mention = (c.mention if (c := guild.get_channel(logging_channel_id)) else "None") if logging_channel_id else "None"

        embed = discord.Embed(title="⚙️ Invite Filter Settings", color=discord.Color.orange()) # Use a different color

        embed.add_field(name="Filter Status", value="✅ Enabled" if delete_invites else "❌ Disabled", inline=False)
        embed.add_field(name="Whitelisted Channels", value=", ".join(whitelisted_channels_mentions) or "None", inline=False)
        embed.add_field(name="Whitelisted Roles", value=", ".join(whitelisted_roles_mentions) or "None", inline=False)
        embed.add_field(name="Logging Channel", value=logging_channel_mention, inline=False)
        embed.add_field(name="Timeout Duration", value=f"{timeout_duration} minutes" + (" (disabled)" if timeout_duration == 0 else ""), inline=False)

        await ctx.send(embed=embed)

