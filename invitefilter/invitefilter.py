import discord
from redbot.core import commands, Config
import re

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
            timeout_duration=1,  # Default to 1 minute
            invites_deleted=0
        )
        self.config.register_global(
            total_invites_deleted=0
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild = message.guild
        if not await self.config.guild(guild).delete_invites():
            return

        if message.channel.id in await self.config.guild(guild).whitelisted_channels():
            return

        whitelisted_roles = await self.config.guild(guild).whitelisted_roles()
        if any(role.id in whitelisted_roles for role in message.author.roles):
            return

        # Enhanced invite pattern to catch variations like ".gg/server"
        invite_pattern = r"(?:https?://)?(?:www\.)?(?:discord(?:app)?\.(?:gg|com/invite)|dsc\.gg|discord\.gg|\.gg)/[a-zA-Z0-9]+"
        match = re.search(invite_pattern, message.content)
        if match:
            actions_taken = []
            try:
                invite_url = match.group(0)
                invite = await self.bot.fetch_invite(invite_url)
                if await self.config.guild(guild).delete_invites():
                    await message.delete()
                    actions_taken.append("Message deleted")
                    # Increment the guild-specific and global invite deletion counters
                    await self.config.guild(guild).invites_deleted.set(
                        await self.config.guild(guild).invites_deleted() + 1
                    )
                    await self.config.total_invites_deleted.set(
                        await self.config.total_invites_deleted() + 1
                    )
                timeout_duration = await self.config.guild(guild).timeout_duration()
                actions_taken.append(f"Timeout issued for {timeout_duration} minutes")
                logging_channel_id = await self.config.guild(guild).logging_channel()
                if logging_channel_id:
                    logging_channel = guild.get_channel(logging_channel_id)
                    if logging_channel:
                        embed = discord.Embed(
                            title="💬 Invite filtration",
                            description="A potentially unwanted invite was detected",
                            color=0xff4545
                        )
                        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                        embed.add_field(name="User", value=message.author.mention, inline=True)
                        embed.add_field(name="Invite", value=invite_url, inline=False)
                        embed.add_field(name="Server name", value=invite.guild.name, inline=True)
                        embed.add_field(name="Server ID", value=invite.guild.id, inline=True)
                        embed.add_field(name="Member count", value=invite.approximate_member_count, inline=True)
                        embed.add_field(name="Online now", value=invite.approximate_presence_count, inline=True)
                        if actions_taken:
                            embed.add_field(name="Actions Taken", value=", ".join(actions_taken), inline=False)
                        await logging_channel.send(embed=embed)
            except discord.Forbidden:
                pass
            except discord.NotFound:
                pass
            except discord.HTTPException:
                pass

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(invoke_without_command=True, aliases=["if"])
    async def invitefilter(self, ctx):
        """Manage the invite filter settings."""
        await ctx.send_help(ctx.command)

    @invitefilter.command()
    async def toggle(self, ctx):
        """Toggle the invite filter on or off."""
        guild = ctx.guild
        current_status = await self.config.guild(guild).delete_invites()
        new_status = not current_status
        await self.config.guild(guild).delete_invites.set(new_status)
        status = "enabled" if new_status else "disabled"
        await ctx.send(f"Invite filter {status}.")

    @invitefilter.group(invoke_without_command=True)
    async def whitelist(self, ctx):
        """Manage the invite filter whitelist."""
        await ctx.send_help(ctx.command)

    @whitelist.command(name="channel")
    async def whitelist_channel(self, ctx, target: discord.TextChannel):
        """Add or remove a channel from the invite filter whitelist."""
        guild = ctx.guild
        whitelisted_channels = await self.config.guild(guild).whitelisted_channels()
        changelog = []

        if target.id in whitelisted_channels:
            whitelisted_channels.remove(target.id)
            changelog.append(f"Removed channel: {target.mention}")
        else:
            whitelisted_channels.append(target.id)
            changelog.append(f"Added channel: {target.mention}")
        await self.config.guild(guild).whitelisted_channels.set(whitelisted_channels)

        if changelog:
            changelog_message = "\n".join(changelog)
            embed = discord.Embed(title="Whitelist Changelog", description=changelog_message, color=discord.Color.blue())
            await ctx.send(embed=embed)

    @whitelist.command(name="role")
    async def whitelist_role(self, ctx, role: discord.Role):
        """Add or remove a role from the invite filter whitelist."""
        guild = ctx.guild
        whitelisted_roles = await self.config.guild(guild).whitelisted_roles()
        changelog = []

        if role.id in whitelisted_roles:
            whitelisted_roles.remove(role.id)
            changelog.append(f"Removed role: {role.name}")
        else:
            whitelisted_roles.append(role.id)
            changelog.append(f"Added role: {role.name}")
        await self.config.guild(guild).whitelisted_roles.set(whitelisted_roles)

        if changelog:
            changelog_message = "\n".join(changelog)
            embed = discord.Embed(title="Whitelist Changelog", description=changelog_message, color=discord.Color.blue())
            await ctx.send(embed=embed)

    @invitefilter.command()
    async def logs(self, ctx, channel: discord.TextChannel):
        """Set the logging channel for invite detections."""
        guild = ctx.guild
        await self.config.guild(guild).logging_channel.set(channel.id)
        await ctx.send(f"Logging channel set to {channel.mention}.")

    @invitefilter.command()
    async def timeout(self, ctx, duration: int):
        """Set the timeout duration for message deletions."""
        guild = ctx.guild
        await self.config.guild(guild).timeout_duration.set(duration)
        await ctx.send(f"Timeout duration set to {duration} minutes.")

    @invitefilter.command()
    async def stats(self, ctx):
        """Display the number of invites deleted and the timeout duration."""
        guild = ctx.guild
        invites_deleted = await self.config.guild(guild).invites_deleted()
        timeout_duration = await self.config.guild(guild).timeout_duration()
        total_invites_deleted = await self.config.total_invites_deleted()
        
        embed = discord.Embed(title="Invite filter stats", color=0xfffffe)
        embed.add_field(name="In this server", value="", inline=False)
        embed.add_field(name="Invites deleted", value=str(invites_deleted), inline=True)
        embed.add_field(name="Time users spent timed out", value=f"{timeout_duration} minutes", inline=False)
        embed.add_field(name="In all servers", value="", inline=False)
        embed.add_field(name="Invites deleted", value=str(total_invites_deleted), inline=False)
        
        await ctx.send(embed=embed)

    @invitefilter.command()
    async def settings(self, ctx):
        """Display the current settings of the invite filter."""
        guild = ctx.guild
        delete_invites = await self.config.guild(guild).delete_invites()
        whitelisted_channels = await self.config.guild(guild).whitelisted_channels()
        whitelisted_roles = await self.config.guild(guild).whitelisted_roles()
        logging_channel_id = await self.config.guild(guild).logging_channel()
        timeout_duration = await self.config.guild(guild).timeout_duration()

        whitelisted_channels_mentions = [guild.get_channel(ch_id).mention for ch_id in whitelisted_channels if guild.get_channel(ch_id)]
        whitelisted_roles_names = [guild.get_role(role_id).name for role_id in whitelisted_roles if guild.get_role(role_id)]
        logging_channel_mention = guild.get_channel(logging_channel_id).mention if logging_channel_id and guild.get_channel(logging_channel_id) else "None"

        embed = discord.Embed(title="Invite filter settings", color=discord.Color.green())
        embed.add_field(name="Delete messages that contain invites", value=":white_check_mark: Enabled" if delete_invites else ":x: Disabled", inline=False)
        embed.add_field(name="Currently whitelisted channels", value=", ".join(whitelisted_channels_mentions) or "None", inline=False)
        embed.add_field(name="Currently whitelisted roles", value=", ".join(whitelisted_roles_names) or "None", inline=False)
        embed.add_field(name="Logging channel", value=logging_channel_mention, inline=False)
        embed.add_field(name="Length of timeouts", value=f"{timeout_duration} minutes", inline=False)

        await ctx.send(embed=embed)

