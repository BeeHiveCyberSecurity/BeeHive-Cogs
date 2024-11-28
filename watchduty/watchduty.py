import discord
from discord.ext import commands

class WatchDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mass_mentions_disabled = False
        self.external_apps_disabled = False

    @commands.command(name="toggle_mass_mentions")
    @commands.has_permissions(administrator=True)
    async def toggle_mass_mentions(self, ctx):
        """Toggle the ability to use mass mentions in the server."""
        self.mass_mentions_disabled = not self.mass_mentions_disabled
        status = "disabled" if self.mass_mentions_disabled else "enabled"

        for guild in self.bot.guilds:
            for role in guild.roles:
                if self.mass_mentions_disabled:
                    # Deny the permission to mention everyone, here, and roles
                    await role.edit(permissions=role.permissions.update(mention_everyone=False))
                else:
                    # Allow the permission to mention everyone, here, and roles
                    await role.edit(permissions=role.permissions.update(mention_everyone=True))

        await ctx.send(f"Mass mentions have been {status}.")

    @commands.command(name="toggle_external_apps")
    @commands.has_permissions(administrator=True)
    async def toggle_external_apps(self, ctx):
        """Toggle the ability to use external apps in the server."""
        self.external_apps_disabled = not self.external_apps_disabled
        status = "disabled" if self.external_apps_disabled else "enabled"

        for guild in self.bot.guilds:
            for role in guild.roles:
                if self.external_apps_disabled:
                    # Deny the permission to use external apps
                    await role.edit(permissions=role.permissions.update(use_external_apps=False))
                else:
                    # Allow the permission to use external apps
                    await role.edit(permissions=role.permissions.update(use_external_apps=True))

        await ctx.send(f"External apps have been {status}.")

def setup(bot):
    bot.add_cog(WatchDuty(bot))
