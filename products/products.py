import asyncio
import discord
from redbot.core import commands


class Products(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="antivirus", description="Learn more about BeeHive's AntiVirus", aliases=["av"])
    async def antivirus(self, ctx: commands.Context):

        embed = discord.Embed(
    title='AntiVirus & AntiMalware',
    description='Description text field',
    colour=16767334,
    url='https://www.beehive.systems/antivirus',
)
    await ctx.send(embed=embed)
    
    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="vulnerabilityscanning", description="Learn more about Vulnerability Scanning", aliases=[""])
    async def vulnerabilityscanning(self, ctx: commands.Context):
        await ctx.send("vuln scanning test message")