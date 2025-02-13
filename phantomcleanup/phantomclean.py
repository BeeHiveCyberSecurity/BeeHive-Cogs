import discord
from redbot.core import commands, checks
from redbot.core.bot import Red
from typing import List
import asyncio

class PhantomClean(commands.Cog):
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
            await ctx.send(f"Attempting to delete channel: {channel.name} {channel.id}")
            try:
                await channel.delete(reason="Cleaning up a raid")
                await ctx.send(f"Deleted channel: {channel.name} {channel.id}")
            except discord.Forbidden:
                await ctx.send(f"Failed to delete channel: {channel.name} {channel.id} (missing permissions)")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to delete channel: {channel.name} {channel.id} (HTTP error: {e})")
            await asyncio.sleep(1)  # Adding a slight delay to prevent rate limiting

    async def unban_users(self, ctx: commands.Context):
        """Unbans all users in the server's banlist."""
        guild = ctx.guild
        bans = [entry async for entry in guild.bans()]
        
        if not bans:
            await ctx.send("No users to unban.")
            return

        total_bans = len(bans)
        await ctx.send(f"Found {total_bans} users to unban. Starting unban process...")

        for i, ban_entry in enumerate(bans, start=1):
            user = ban_entry.user
            await ctx.send(f"Attempting to unban {user.name}#{user.discriminator} ({i}/{total_bans})")
            try:
                await guild.unban(user, reason="Cleaning up a raid")
                await ctx.send(f"Unbanned {user.name}#{user.discriminator} ({i}/{total_bans})")
            except discord.Forbidden:
                await ctx.send(f"Failed to unban {user.name}#{user.discriminator} (missing permissions)")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to unban {user.name}#{user.discriminator} (HTTP error: {e})")
            await asyncio.sleep(1)  # Adding a slight delay to prevent rate limiting
