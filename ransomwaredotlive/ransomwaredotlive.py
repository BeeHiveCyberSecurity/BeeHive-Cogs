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
                    embed.description = item['description']
                    embed.add_field(name="Activity", value=item['activity'], inline=False)
                    embed.add_field(name="Country", value=item['country'], inline=False)
                    embed.add_field(name="Discovered", value=f"<t:{int(item['discovered'])}:R>", inline=False)
                    embed.add_field(name="Group Name", value=item['group_name'], inline=False)
                    embed.add_field(name="Published", value=f"<t:{int(item['published'])}:R>", inline=False)
                    embed.add_field(name="Website", value=item['website'], inline=False)
                    embed.add_field(name="More Info", value=f"[More Info]({item['post_url']})", inline=False)
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
