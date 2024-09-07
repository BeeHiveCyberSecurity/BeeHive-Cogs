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
                pages = []
                for item in data:
                    embed = discord.Embed(title=item["post_title"], color=discord.Color.red())
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
                    embed.description = description
                    pages.append(embed)

                message = await ctx.send(embed=pages[0])

                emojis = ['⬅️', '➡️', '❌']
                for emoji in emojis:
                    await message.add_reaction(emoji)

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in emojis and reaction.message.id == message.id

                current_page = 0
                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                        if str(reaction.emoji) == '⬅️':
                            current_page = (current_page - 1) % len(pages)
                            await message.edit(embed=pages[current_page])
                        elif str(reaction.emoji) == '➡️':
                            current_page = (current_page + 1) % len(pages)
                            await message.edit(embed=pages[current_page])
                        elif str(reaction.emoji) == '❌':
                            await message.delete()
                            break

                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break
