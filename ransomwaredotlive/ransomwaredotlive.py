import discord #type: ignore
from redbot.core import commands #type: ignore
import aiohttp #type: ignore
import asyncio
import datetime

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
                    embed = discord.Embed(title=item["post_title"], color=0xfffffe)
                    embed.description = item['description']
                    
                    if 'activity' in item:
                        embed.add_field(name="Activity", value=item['activity'], inline=False)
                    if 'country' in item:
                        embed.add_field(name="Country", value=item['country'], inline=False)
                    
                    # Convert datetime string to timestamp
                    if 'published' in item:
                        published_timestamp = int(datetime.datetime.strptime(item['published'], "%Y-%m-%d %H:%M:%S.%f").timestamp())
                        embed.add_field(name="Published by hackers", value=f"<t:{published_timestamp}:R>", inline=False)
                    if 'discovered' in item:
                        discovered_timestamp = int(datetime.datetime.strptime(item['discovered'], "%Y-%m-%d %H:%M:%S.%f").timestamp())
                        embed.add_field(name="Discovered by indexer", value=f"<t:{discovered_timestamp}:R>", inline=False)
                    if 'group_name' in item:
                        embed.add_field(name="Group Name", value=item['group_name'], inline=False)
                    if 'website' in item:
                        embed.add_field(name="Website", value=item['website'], inline=False)
                    
                    pages.append(embed)

                message = await ctx.send(embed=pages[0])

                # Add URL button if post_url is present
                if 'post_url' in data[0]:
                    view = discord.ui.View()
                    button = discord.ui.Button(label="Read the leak post", url=data[0]['post_url'])
                    view.add_item(button)
                    await message.edit(view=view)

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
                        for emoji in emojis:
                            await message.remove_reaction(emoji, self.bot.user)
                        break
