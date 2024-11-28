import discord
from redbot.core import commands
import asyncio

class WatchDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="watchduty", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def watchduty_group(self, ctx):
        """Base command for WatchDuty settings."""
        await ctx.send_help(ctx.command)

    async def update_progress_embed(self, ctx, title, description, color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        message = await ctx.send(embed=embed)
        return message

    async def edit_progress_embed(self, message, title, description, color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        await message.edit(embed=embed)

    @watchduty_group.command(name="massmentions")
    async def disable_mass_mentions(self, ctx):
        """Disable the ability to use mass mentions in the server."""
        roles_modified = 0
        roles_skipped = 0
        roles_ignored = 0
        progress_message = await self.update_progress_embed(
            ctx,
            "Disabling Mass Mentions",
            "Starting the process...",
            discord.Color.orange()
        )
        for guild in self.bot.guilds:
            for role in guild.roles:
                if guild.me.top_role > role and not role.permissions.administrator and not role.permissions.manage_guild:
                    try:
                        # Deny the permission to mention everyone, here, and roles
                        new_permissions = role.permissions
                        new_permissions.update(mention_everyone=False)
                        await role.edit(permissions=new_permissions)
                        roles_modified += 1
                    except discord.errors.Forbidden:
                        roles_skipped += 1
                        continue
                else:
                    roles_ignored += 1
                await self.edit_progress_embed(
                    progress_message,
                    "Making permissions changes to protect the server, please wait...",
                    f"Processing... {roles_modified} roles modified, {roles_skipped} roles skipped, {roles_ignored} roles ignored.",
                    discord.Color.orange()
                )
                await asyncio.sleep(3)  # Respect rate limits

        await self.edit_progress_embed(
            progress_message,
            "Permission changes finished",
            f"Mass mentions have been disabled for {roles_modified} roles. {roles_skipped} roles could not be modified due to missing permissions. {roles_ignored} roles were ignored.",
            discord.Color.red()
        )

    @watchduty_group.command(name="externalapps")
    async def disable_external_apps(self, ctx):
        """Disable the ability to use external apps in the server."""
        roles_modified = 0
        roles_skipped = 0
        roles_ignored = 0
        progress_message = await self.update_progress_embed(
            ctx,
            "Disabling External Apps",
            "Starting the process...",
            discord.Color.orange()
        )
        for guild in self.bot.guilds:
            for role in guild.roles:
                if guild.me.top_role > role and not role.permissions.administrator and not role.permissions.manage_guild:
                    try:
                        # Deny the permission to use external apps
                        new_permissions = role.permissions
                        new_permissions.update(use_external_apps=False)
                        await role.edit(permissions=new_permissions)
                        roles_modified += 1
                    except discord.errors.Forbidden:
                        roles_skipped += 1
                        continue
                else:
                    roles_ignored += 1
                await self.edit_progress_embed(
                    progress_message,
                    "Making permissions changes to protect the server, please wait...",
                    f"Processing... {roles_modified} roles modified, {roles_skipped} roles skipped, {roles_ignored} roles ignored.",
                    discord.Color.orange()
                )
                await asyncio.sleep(1)  # Respect rate limits

        await self.edit_progress_embed(
            progress_message,
            "Permissions changes finished",
            f"External apps have been disabled for {roles_modified} roles. {roles_skipped} roles could not be modified due to missing permissions. {roles_ignored} roles were ignored.",
            discord.Color.red()
        )

async def setup(bot):
    await bot.add_cog(WatchDuty(bot))
