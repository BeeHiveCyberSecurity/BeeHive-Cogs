from redbot.core import Config, commands
import discord
from discord.ui import View

class Orchestrator(commands.Cog):
    """See info about the servers your bot is in.
    
    For bot owners only.
    """

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=806715409318936616)
        self.bot = bot

    # This cog does not store any End User Data
    async def red_get_data_for_user(self, *, user_id: int):
        return {}
    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        pass

        @commands.command(name="serversinfo")
        @commands.is_owner()
        async def serversinfo(self, ctx):
            """Shows information about the servers the bot is in."""
            servers = self.bot.guilds
            embed = discord.Embed(title="Server Information", color=discord.Color.blue())
            for server in servers:
                embed.add_field(name=server.name, value=f"ID: {server.id}\nMembers: {server.member_count}", inline=False)
            await ctx.send(embed=embed)

        @commands.command(name="leaveserver")
        @commands.is_owner()
        async def leaveserver(self, ctx, server_id: int):
            """Makes the bot leave a specified server."""
            server = self.bot.get_guild(server_id)
            if server:
                await server.leave()
                await ctx.send(f"Left the server: {server.name}")
            else:
                await ctx.send("Server not found.")

