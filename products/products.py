from redbot.core import commands
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle

class Products(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="antivirus", description="Learn more about BeeHive's AntiVirus", aliases=["av"])
    async def antivirus(self, ctx: commands.Context):
        buttons = [
            create_button(
                style=ButtonStyle.green,
                label="A Green Button"
            ),
          ]
        action_row = create_actionrow(*buttons)
        await ctx.send("antivirus test message lol", components=[action_row])
    
    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="vulnerabilityscanning", description="Learn more about Vulnerability Scanning", aliases=[""])
    async def vulnerabilityscanning(self, ctx: commands.Context):
        await ctx.send("vuln scanning test message")