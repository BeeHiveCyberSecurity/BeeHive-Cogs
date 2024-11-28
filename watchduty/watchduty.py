import discord
from redbot.core import commands

class WatchDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="watchduty")
    @commands.has_permissions(administrator=True)
    async def watchduty_group(self, ctx):
        """Base command for WatchDuty settings."""

    @watchduty_group.command(name="massmentions")
    async def disable_mass_mentions(self, ctx):
        """Disable the ability to use mass mentions in the server."""
        roles_modified = 0
        for guild in self.bot.guilds:
            for role in guild.roles:
                if guild.me.top_role > role:  # Check if the bot has permission to edit the role
                    # Deny the permission to mention everyone, here, and roles
                    await role.edit(permissions=role.permissions.update(mention_everyone=False))
                    roles_modified += 1

        await ctx.send(f"Mass mentions have been disabled for {roles_modified} roles.")

    @watchduty_group.command(name="externalapps")
    async def disable_external_apps(self, ctx):
        """Disable the ability to use external apps in the server."""
        roles_modified = 0
        for guild in self.bot.guilds:
            for role in guild.roles:
                if guild.me.top_role > role:  # Check if the bot has permission to edit the role
                    # Deny the permission to use external apps
                    await role.edit(permissions=role.permissions.update(use_external_apps=False))
                    roles_modified += 1

        await ctx.send(f"External apps have been disabled for {roles_modified} roles.")

async def setup(bot):
    await bot.add_cog(WatchDuty(bot))
