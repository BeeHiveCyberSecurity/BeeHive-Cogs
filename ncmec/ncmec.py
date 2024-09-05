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

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    data = await response.json()
                elif 'text/xml' in content_type or 'application/xml' in content_type:
                    text = await response.text()
                    data = await self.parse_xml(text)
                else:
                    await ctx.send("Received unexpected content type from the MissingKids API.")
                    return

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

    async def parse_xml(self, text):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(text)
        children = []
        for child in root.findall('.//child'):
            children.append({
                'name': child.find('name').text if child.find('name') is not None else 'Unknown',
                'age': child.find('age').text if child.find('age') is not None else 'Unknown',
                'gender': child.find('gender').text if child.find('gender') is not None else 'Unknown',
                'missingSince': child.find('missingSince').text if child.find('missingSince') is not None else 'Unknown',
                'location': child.find('location').text if child.find('location') is not None else 'Unknown',
            })
        return {'children': children}

