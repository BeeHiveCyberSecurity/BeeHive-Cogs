from redbot.core import commands, Config
import discord

class VanityGuard(commands.Cog):
    """A cog to protect the server's vanity URL."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled": True,
            "auto_revert": False
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
        if current_vanity:
            await self.config.guild(guild).vanity_url.set(current_vanity)
            await ctx.send(f"Vanity URL protection has been enabled for: discord.gg/{current_vanity}")
        else:
            await ctx.send("Vanity URL protection has been enabled, but no vanity URL is currently set.")

    @vanityguard.command()
    async def disable(self, ctx):
        """Disable the vanity URL protection."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Vanity URL protection has been disabled.")

    @vanityguard.command()
    async def autorevert(self, ctx):
        """Toggle automatic reverts to vanity URL changes."""
        guild = ctx.guild
        current_setting = await self.config.guild(guild).auto_revert()
        new_setting = not current_setting
        await self.config.guild(guild).auto_revert.set(new_setting)
        status = "enabled" if new_setting else "disabled"
        await ctx.send(f"Automatic reverts to vanity URL changes have been {status}.")

    @vanityguard.command()
    async def check(self, ctx):
        """Check if the vanity URL is still set correctly."""
        guild = ctx.guild
        if not await self.config.guild(guild).enabled():
            await ctx.send("Vanity URL protection is currently disabled.")
            return

        # Check if the server has a vanity URL feature
        if not guild.features or "VANITY_URL" not in guild.features:
            await ctx.send("This server does not have a vanity URL feature.")
            return

        # Use await vanity_invite() to fetch the currently set vanity
        vanity_invite = await guild.vanity_invite()
        current_vanity = vanity_invite.code if vanity_invite else None

        if current_vanity is None:
            await ctx.send("This server does not currently have a vanity URL set.")
            return

        protected_vanity = await self.config.guild(guild).vanity_url()  # Fetch the protected vanity from config

        if current_vanity == protected_vanity:
            await ctx.send(f"The vanity URL is correctly set to: discord.gg/{current_vanity}")
        else:
            await ctx.send(f"Warning: The vanity URL has changed! Current: discord.gg/{current_vanity}, Expected: discord.gg/{protected_vanity}")

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
                # Notify the server owner or take action
                owner = after.owner
                if owner:
                    try:
                        await owner.send(f"Warning: The vanity URL has changed! Current: {after_vanity_code}, Expected: {protected_vanity}")
                    except discord.Forbidden:
                        pass

                # Automatically revert the vanity URL if auto_revert is enabled
                if await self.config.guild(after).auto_revert():
                    try:
                        await after.edit(vanity_url_code=protected_vanity)
                        await owner.send("The vanity URL has been automatically reverted to the protected value.")
                    except (discord.Forbidden, discord.HTTPException):
                        await owner.send("Failed to automatically revert the vanity URL. Please check permissions.")
