import discord
from redbot.core import commands, checks
from redbot.core.bot import Red
from typing import List

class PhantomCleanup(commands.Cog):
    """A cog to clean up phantom logger raids."""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    @checks.mod_or_permissions(manage_guild=True)
    async def phantomclean(self, ctx: commands.Context):
        """Cleans up phantom logger channels and unbans users."""
        await ctx.send("Starting cleanup process...")

        # Step 1: Find and delete channels named "phantom-logger"
        await self.delete_phantom_logger_channels(ctx)

        # Step 2: Unban users from the server's banlist
        await self.unban_users(ctx)

        await ctx.send("Cleanup process completed.")

    async def delete_phantom_logger_channels(self, ctx: commands.Context):
        """Deletes channels named 'phantom-logger'."""
        guild = ctx.guild
        phantom_channels = [channel for channel in guild.channels if channel.name == "phantom-logger"]
        
        if not phantom_channels:
            await ctx.send("No 'phantom-logger' channels found.")
            return

        for channel in phantom_channels:
            try:
                await channel.delete()
                await ctx.send(f"Deleted channel: {channel.name}")
            except discord.Forbidden:
                await ctx.send(f"Failed to delete channel: {channel.name} (missing permissions)")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to delete channel: {channel.name} (HTTP error: {e})")

    async def unban_users(self, ctx: commands.Context):
        """Unbans all users in the server's banlist."""
        guild = ctx.guild
        bans = await guild.bans()
        
        if not bans:
            await ctx.send("No users to unban.")
            return

        total_bans = len(bans)
        await ctx.send(f"Found {total_bans} users to unban. Starting unban process...")

        for i, ban_entry in enumerate(bans, start=1):
            user = ban_entry.user
            try:
                await guild.unban(user)
                await ctx.send(f"Unbanned {user.name}#{user.discriminator} ({i}/{total_bans})")
            except discord.Forbidden:
                await ctx.send(f"Failed to unban {user.name}#{user.discriminator} (missing permissions)")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to unban {user.name}#{user.discriminator} (HTTP error: {e})")
