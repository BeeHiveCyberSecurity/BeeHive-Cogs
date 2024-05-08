from redbot.core import Config, commands
import discord
from discord.ui import Button, View

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
        await ctx.defer()
        guilds = [guild async for guild in self.bot.fetch_guilds(limit=None)]
        guilds_sorted = sorted(guilds, key=lambda x: x.approximate_member_count, reverse=True)
        
        embeds = []
        for guild in guilds_sorted:
            embed = discord.Embed(title=guild.name, description=f"Members: {guild.approximate_member_count}\nActive: {guild.approximate_presence_count}")
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(name="Guild ID", value=guild.id)
            embeds.append(embed)
        
        if not embeds:
            return await ctx.send("No guilds available.")
        
        # Paginator view with buttons
        class PaginatorView(View):
            def __init__(self, embeds):
                super().__init__()
                self.embeds = embeds
                self.current_page = 0
                self.add_item(Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous_btn"))
                self.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_btn"))
            
            async def interaction_check(self, interaction):
                return interaction.user == ctx.author
            
            @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous_btn")
            async def previous_button_callback(self, button, interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
            
            @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_btn")
            async def next_button_callback(self, button, interaction):
                if self.current_page < len(self.embeds) - 1:
                    self.current_page += 1
                    await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        
        await ctx.send(embed=embeds[0], view=PaginatorView(embeds))
