from redbot.core import commands, Config
import discord

class VanityGuard(commands.Cog):
    """A cog to protect the server's vanity URL."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=999)
        default_guild = {
            "enabled": True,
            "auto_revert": False,
            "alert_channel": None,
            "tamper_action": "none",  # Default action is none
            "vanity_url": None  # Add missing default for vanity_url
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(invoke_without_command=True)
    async def vanityguard(self, ctx):
        """Commands for managing the vanity URL protection."""
        await ctx.send_help(ctx.command)

    @vanityguard.command()
    async def enable(self, ctx):
        """Enable the vanity URL protection."""
        guild = ctx.guild
        await self.config.guild(guild).enabled.set(True)
        # Set the current vanity URL as the protected one
        vanity_invite = await guild.vanity_invite()
        current_vanity = vanity_invite.code if vanity_invite else None
        embed = discord.Embed(title="Vanity URL Protection", color=discord.Color.green())
        if current_vanity:
            await self.config.guild(guild).vanity_url.set(current_vanity)
            embed.description = f"Vanity URL protection has been enabled for: discord.gg/{current_vanity}"
        else:
            embed.description = "Vanity URL protection has been enabled, but no vanity URL is currently set."
        await ctx.send(embed=embed)

    @vanityguard.command()
    async def disable(self, ctx):
        """Disable the vanity URL protection."""
        await self.config.guild(ctx.guild).enabled.set(False)
        embed = discord.Embed(title="Vanity URL Protection", description="Vanity URL protection has been disabled.", color=discord.Color.red())
        await ctx.send(embed=embed)

    @vanityguard.command()
    async def autorevert(self, ctx):
        """Toggle automatic reverts to vanity URL changes."""
        guild = ctx.guild
        current_setting = await self.config.guild(guild).auto_revert()
        new_setting = not current_setting
        await self.config.guild(guild).auto_revert.set(new_setting)
        status = "enabled" if new_setting else "disabled"
        embed = discord.Embed(title="Automatic Revert", description=f"Automatic reverts to vanity URL changes have been {status}.", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @vanityguard.command()
    async def check(self, ctx):
        """Check if the vanity URL is still set correctly."""
        guild = ctx.guild
        if not await self.config.guild(guild).enabled():
            embed = discord.Embed(title="Vanity URL Check", description="Vanity URL protection is currently disabled.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        # Check if the server has a vanity URL feature
        if not guild.features or "VANITY_URL" not in guild.features:
            embed = discord.Embed(title="Vanity URL Check", description="This server does not have a vanity URL feature.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        # Use await vanity_invite() to fetch the currently set vanity
        vanity_invite = await guild.vanity_invite()
        current_vanity = vanity_invite.code if vanity_invite else None

        if current_vanity is None:
            embed = discord.Embed(title="Vanity URL Check", description="This server does not currently have a vanity URL set.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        protected_vanity = await self.config.guild(guild).vanity_url()  # Fetch the protected vanity from config

        embed = discord.Embed(title="Vanity URL Check", color=discord.Color.green() if current_vanity == protected_vanity else discord.Color.red())
        if current_vanity == protected_vanity:
            embed.description = f"The vanity URL is correctly set to: discord.gg/{current_vanity}"
        else:
            embed.description = f"Warning: The vanity URL has changed! Current: discord.gg/{current_vanity}, Expected: discord.gg/{protected_vanity}"
        await ctx.send(embed=embed)

    @vanityguard.command()
    async def alerts(self, ctx, channel: discord.TextChannel):
        """Set the channel for vanity URL alerts."""
        await self.config.guild(ctx.guild).alert_channel.set(channel.id)
        embed = discord.Embed(title="Alert Channel Set", description=f"Vanity URL alerts will be sent to {channel.mention}.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @vanityguard.command()
    async def action(self, ctx, action: str):
        """Set the action to take against users who tamper with the vanity URL."""
        valid_actions = ["timeout", "kick", "ban", "strip_roles", "none"]
        if action not in valid_actions:
            await ctx.send(f"Invalid action. Choose from: {', '.join(valid_actions)}")
            return
        await self.config.guild(ctx.guild).tamper_action.set(action)
        embed = discord.Embed(title="Tamper Action Set", description=f"Action for tampering with vanity URL set to: {action}", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Check vanity URL on guild update."""
        if not await self.config.guild(after).enabled():
            return

        # Use await vanity_invite() to fetch the currently set vanity
        before_vanity_invite = await before.vanity_invite()
        after_vanity_invite = await after.vanity_invite()
        before_vanity_code = before_vanity_invite.code if before_vanity_invite else None
        after_vanity_code = after_vanity_invite.code if after_vanity_invite else None

        if before_vanity_code != after_vanity_code:
            protected_vanity = await self.config.guild(after).vanity_url()
            if protected_vanity and after_vanity_code != protected_vanity:
                alert_channel_id = await self.config.guild(after).alert_channel()
                alert_channel = after.get_channel(alert_channel_id)
                if alert_channel:
                    try:
                        embed = discord.Embed(title="Vanity URL Alert", description=f"Warning: The vanity URL has changed! Current: {after_vanity_code}, Expected: {protected_vanity}", color=discord.Color.red())
                        await alert_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass

                # Handle tamper action
                tamper_action = await self.config.guild(after).tamper_action()
                if tamper_action and tamper_action != "none":
                    for member in after.members:
                        if member.guild_permissions.manage_guild:
                            try:
                                if tamper_action == "timeout":
                                    await member.timeout(duration=60)  # Example: timeout for 60 seconds
                                elif tamper_action == "kick":
                                    await member.kick(reason="Tampering with vanity URL")
                                elif tamper_action == "ban":
                                    await member.ban(reason="Tampering with vanity URL")
                                elif tamper_action == "strip_roles":
                                    await member.edit(roles=[])
                            except discord.Forbidden:
                                if alert_channel:
                                    embed = discord.Embed(title="Tamper Action Failed", description=f"Failed to perform {tamper_action} on {member.mention}. Please check permissions.", color=discord.Color.red())
                                    await alert_channel.send(embed=embed)

                # Automatically revert the vanity URL if auto_revert is enabled
                if await self.config.guild(after).auto_revert():
                    try:
                        await after.edit(vanity_url_code=protected_vanity)
                        embed = discord.Embed(title="Vanity URL Revert", description="The vanity URL has been automatically reverted to the protected value.", color=discord.Color.green())
                        if alert_channel:
                            await alert_channel.send(embed=embed)
                    except (discord.Forbidden, discord.HTTPException):
                        if alert_channel:
                            embed = discord.Embed(title="Vanity URL Revert Failed", description="Failed to automatically revert the vanity URL. Please check permissions.", color=discord.Color.red())
                            await alert_channel.send(embed=embed)
