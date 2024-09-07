import discord
from redbot.core import commands
import aiohttp

class RansomwareDotLive(commands.Cog):
    """Interact with the ransomware.live API"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def ransomware(self, ctx):
        """Ransomware.live API commands"""
        pass

    @ransomware.command()
    async def latest(self, ctx):
        """Get the latest ransomware information"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.ransomware.live/recentvictims") as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch data from ransomware.live API.")
                    return

                data = await response.json()
                embed = discord.Embed(title="Recent Ransomware Victims", color=discord.Color.red())
                for item in data:
                    description = (
                        f"**Activity:** {item['activity']}\n"
                        f"**Country:** {item['country']}\n"
                        f"**Description:** {item['description']}\n"
                        f"**Discovered:** {item['discovered']}\n"
                        f"**Group Name:** {item['group_name']}\n"
                        f"**Published:** {item['published']}\n"
                        f"**Website:** {item['website']}\n"
                        f"[More Info]({item['post_url']})"
                    )
                    embed.add_field(name=item["post_title"], value=description, inline=False)

                await ctx.send(embed=embed)
