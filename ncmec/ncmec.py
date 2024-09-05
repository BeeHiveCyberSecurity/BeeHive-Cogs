import discord
from redbot.core import commands
import aiohttp

class MissingKids(commands.Cog):
    """Cog to interact with the National Center for Missing and Exploited Children"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def ncmec(self, ctx):
        """Primary command group"""
        pass

    @ncmec.command()
    async def recent(self, ctx):
        """Fetch information about recently missing children."""
        url = "https://api.missingkids.org/missingkids/servlet/JSONDataServlet?action=publicSearch"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch data from the MissingKids API.")
                    return

                data = await response.json()
                if not data.get("children"):
                    await ctx.send("No recently missing children found.")
                    return

                embed = discord.Embed(title="Recently Missing Children", color=discord.Color.red())
                for child in data["children"][:10]:  # Limit to first 10 results
                    embed.add_field(
                        name=child.get("name", "Unknown"),
                        value=f"Age: {child.get('age', 'Unknown')}\n"
                              f"Gender: {child.get('gender', 'Unknown')}\n"
                              f"Missing Since: {child.get('missingSince', 'Unknown')}\n"
                              f"Location: {child.get('location', 'Unknown')}",
                        inline=False
                    )

                await ctx.send(embed=embed)

