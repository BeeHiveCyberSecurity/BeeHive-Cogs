from redbot.core import commands, Config
import discord
import aiohttp
import asyncio

class OpenBanList(commands.Cog):
    """
    OpenBanlist is a project aimed at cataloging malicious Discord users and working to keep them out of servers in a united fashion.
    
    For more information or to report a user, please visit [openbanlist.cc](<https://openbanlist.cc>)
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled": False,
            "action": "none",  # Default action is none
            "log_channel": None  # Default log channel is None
        }
        self.config.register_guild(**default_guild)
        self.banlist_url = "https://openbanlist.cc/data/banlist.json"
        self.session = aiohttp.ClientSession()
        self.bot.loop.create_task(self.update_banlist_periodically())

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def banlist(self, ctx):
        """Commands for managing the global banlist."""
        await ctx.send_help(ctx.command)

    @commands.admin_or_permissions(manage_guild=True)
    @banlist.command()
    async def enable(self, ctx):
        """Enable the global banlist protection."""
        await self.config.guild(ctx.guild).enabled.set(True)
        embed = discord.Embed(
            title="Banlist Enabled",
            description="Global banlist protection has been enabled.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.admin_or_permissions(manage_guild=True)
    @banlist.command()
    async def disable(self, ctx):
        """Disable the global banlist protection."""
        await self.config.guild(ctx.guild).enabled.set(False)
        embed = discord.Embed(
            title="Banlist Disabled",
            description="Global banlist protection has been disabled.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.admin_or_permissions(manage_guild=True)
    @banlist.command()
    async def action(self, ctx, action: str):
        """Set the action to take against users on the banlist."""
        valid_actions = ["kick", "ban", "none"]
        if action not in valid_actions:
            embed = discord.Embed(
                title="Invalid Action",
                description=f"Invalid action. Choose from: {', '.join(valid_actions)}",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        await self.config.guild(ctx.guild).action.set(action)
        embed = discord.Embed(
            title="Action Set",
            description=f"Action for users on the banlist set to: {action}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.admin_or_permissions(manage_guild=True)
    @banlist.command()
    async def logs(self, ctx, channel: discord.TextChannel):
        """Set the logging channel for banlist actions."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        embed = discord.Embed(
            title="Log Channel Set",
            description=f"Logging channel set to {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @banlist.command()
    async def check(self, ctx, user_id: int = None):
        """Check if a user is on the global banlist."""
        if user_id is None:
            user_id = ctx.author.id

        async with self.session.get(self.banlist_url) as response:
            if response.status == 200:
                banlist_data = await response.json()
                ban_info = next((ban_info for ban_info in banlist_data.values() if int(ban_info["reported_id"]) == user_id), None)
                
                if ban_info:
                    embed = discord.Embed(
                        title="Banlist Check",
                        description=f"User ID {user_id} is on the banlist.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Ban Reason", value=ban_info.get("ban_reason", "No reason provided"), inline=False)
                    embed.add_field(name="Reporter ID", value=ban_info.get("reporter_id", "Unknown"), inline=False)
                    embed.add_field(name="Approver ID", value=ban_info.get("approver_id", "Unknown"), inline=False)
                    embed.add_field(name="Appealable", value=str(ban_info.get("appealable", False)), inline=False)
                else:
                    embed = discord.Embed(
                        title="Banlist Check",
                        description=f"User ID {user_id} is not on the banlist.",
                        color=discord.Color.green()
                    )
                await ctx.send(embed=embed)

    async def update_banlist_periodically(self):
        while True:
            await self.update_banlist()
            await asyncio.sleep(86400)  # 24 hours

    async def update_banlist(self):
        async with self.session.get(self.banlist_url) as response:
            if response.status == 200:
                banlist_data = await response.json()
                for guild in self.bot.guilds:
                    if await self.config.guild(guild).enabled():
                        await self.enforce_banlist(guild, banlist_data)

    async def enforce_banlist(self, guild, banlist_data):
        action = await self.config.guild(guild).action()
        if action == "none":
            return

        for member in guild.members:
            if any(member.id == int(ban_info["reported_id"]) for ban_info in banlist_data.values()):
                try:
                    if action == "kick":
                        await member.kick(reason="User is on the global banlist.")
                    elif action == "ban":
                        await member.ban(reason="User is on the global banlist.")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if not await self.config.guild(guild).enabled():
            return

        async with self.session.get(self.banlist_url) as response:
            if response.status == 200:
                banlist_data = await response.json()
                log_channel_id = await self.config.guild(guild).log_channel()
                log_channel = guild.get_channel(log_channel_id)

                if any(member.id == int(ban_info["reported_id"]) for ban_info in banlist_data.values()):
                    action = await self.config.guild(guild).action()
                    ban_info = next(ban_info for ban_info in banlist_data.values() if member.id == int(ban_info["reported_id"]))
                    try:
                        if action == "kick":
                            await member.kick(reason="User is on the global banlist.")
                            action_taken = "kicked"
                        elif action == "ban":
                            await member.ban(reason="User is on the global banlist.")
                            action_taken = "banned"
                        else:
                            action_taken = "none"
                    except discord.Forbidden:
                        action_taken = "failed due to permissions"

                    if log_channel:
                        embed = discord.Embed(
                            title="Banlist Alert",
                            description=f"User {member.mention} ({member.id}) joined and is on the banlist.",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Action Taken", value=action_taken, inline=False)
                        embed.add_field(name="Ban Reason", value=ban_info.get("ban_reason", "No reason provided"), inline=False)
                        embed.add_field(name="Reporter ID", value=ban_info.get("reporter_id", "Unknown"), inline=False)
                        embed.add_field(name="Approver ID", value=ban_info.get("approver_id", "Unknown"), inline=False)
                        embed.add_field(name="Appealable", value=str(ban_info.get("appealable", False)), inline=False)
                        await log_channel.send(embed=embed)
                else:
                    if log_channel:
                        embed = discord.Embed(
                            title="Member Joined",
                            description=f"User {member.mention} ({member.id}) joined and is not on the banlist.",
                            color=discord.Color.green()
                        )
                        await log_channel.send(embed=embed)
