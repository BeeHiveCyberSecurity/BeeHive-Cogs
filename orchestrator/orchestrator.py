from redbot.core import Config, app_commands, commands, checks
import discord

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


    @commands.hybrid_command(name="orchestrator", aliases=["botservers"])
    @commands.is_owner()
    async def orchestrator(self, ctx):
        """See and manage the servers that your bot instance is in."""
        await ctx.message.add_reaction("⏳")
        guilds = [guild async for guild in self.bot.fetch_guilds(limit=None)]
        guilds_sorted = sorted(guilds, key=lambda x: x.approximate_member_count, reverse=True)
        
        total_guild_count = len(guilds)
        total_member_count = sum(guild.approximate_member_count for guild in guilds_sorted)
        
        embeds = []
        for guild in guilds_sorted:
            embed = discord.Embed(title=guild.name, description=f"Members: {guild.approximate_member_count}\nActive: {guild.approximate_presence_count}")
            embed.add_field(name="Guild ID", value=guild.id)
            embeds.append(embed)
        
        await ctx.message.clear_reaction("⏳")
        
        if not embeds:
            return await ctx.send("No guilds available.")
        
        # Paginator class to be implemented or imported
        paginator = Paginator(pages=embeds, timeout=60.0)
        await paginator.start(ctx)
