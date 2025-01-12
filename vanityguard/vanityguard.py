from redbot.core import commands, Config
import discord

class VanityGuard(commands.Cog):
    """A cog to protect the server's vanity URL."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "vanity_url": None
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(invoke_without_command=True)
    async def vanityguard(self, ctx):
        """Commands for managing the vanity URL protection."""
        await ctx.send_help(ctx.command)

    @vanityguard.command()
    async def check(self, ctx):
        """Check if the vanity URL is still set correctly."""
        guild = ctx.guild
        current_vanity = guild.vanity_url_code
        protected_vanity = current_vanity  # Assume the current vanity is the one to protect

        if protected_vanity is None:
            await ctx.send("No vanity URL is currently set.")
            return

        if current_vanity == protected_vanity:
            await ctx.send("The vanity URL is correctly set.")
        else:
            await ctx.send(f"Warning: The vanity URL has changed! Current: {current_vanity}, Expected: {protected_vanity}")

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Check vanity URL on guild update."""
        if before.vanity_url_code != after.vanity_url_code:
            protected_vanity = await self.config.guild(after).vanity_url()
            if protected_vanity and after.vanity_url_code != protected_vanity:
                # Notify the server owner or take action
                owner = after.owner
                if owner:
                    try:
                        await owner.send(f"Warning: The vanity URL has changed! Current: {after.vanity_url_code}, Expected: {protected_vanity}")
                    except discord.Forbidden:
                        pass
