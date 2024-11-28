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
        roles_skipped = 0
        for guild in self.bot.guilds:
            for role in guild.roles:
                if guild.me.top_role > role:  # Check if the bot has permission to edit the role
                    try:
                        # Deny the permission to mention everyone, here, and roles
                        new_permissions = role.permissions
                        new_permissions.update(mention_everyone=False)
                        await role.edit(permissions=new_permissions)
                        roles_modified += 1
                    except discord.errors.Forbidden:
                        roles_skipped += 1
                        continue

        embed = discord.Embed(
            title="Mass Mentions Disabled",
            description=f"Mass mentions have been disabled for {roles_modified} roles. {roles_skipped} roles could not be modified due to missing permissions.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @watchduty_group.command(name="externalapps")
    async def disable_external_apps(self, ctx):
        """Disable the ability to use external apps in the server."""
        roles_modified = 0
        roles_skipped = 0
        for guild in self.bot.guilds:
            for role in guild.roles:
                if guild.me.top_role > role:  # Check if the bot has permission to edit the role
                    try:
                        # Deny the permission to use external apps
                        new_permissions = role.permissions
                        new_permissions.update(use_external_apps=False)
                        await role.edit(permissions=new_permissions)
                        roles_modified += 1
                    except discord.errors.Forbidden:
                        roles_skipped += 1
                        continue

        embed = discord.Embed(
            title="External Apps Disabled",
            description=f"External apps have been disabled for {roles_modified} roles. {roles_skipped} roles could not be modified due to missing permissions.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WatchDuty(bot))
