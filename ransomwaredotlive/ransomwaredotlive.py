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
    async def groups(self, ctx):
        """Get the list of ransomware groups"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.ransomware.live/groups") as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch data from ransomware.live API.")
                    return

                data = await response.json()
                pages = []
                for group in data:
                    embed = discord.Embed(title=group["name"], color=0xfffffe)
                    
                    if 'description' in group and group['description']:
                        embed.description = group['description']
                    
                    if 'locations' in group:
                        for location in group['locations']:
                            status = "Available" if location['available'] else "Unavailable"
                            embed.add_field(name=location['title'], value=f"URL: {location['slug']}\nStatus: {status}", inline=False)
                    
                    if 'profile' in group and group['profile']:
                        for profile_link in group['profile']:
                            embed.add_field(name="Profile", value=profile_link, inline=False)
                    
                    pages.append(embed)

                message = await ctx.send(embed=pages[0])

                # Add navigation reactions if there are multiple pages
                if len(pages) > 1:
                    await message.add_reaction("⬅️")
                    await message.add_reaction("➡️")

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

                    current_page = 0
                    while True:
                        try:
                            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                            if str(reaction.emoji) == "⬅️":
                                current_page = (current_page - 1) % len(pages)
                            elif str(reaction.emoji) == "➡️":
                                current_page = (current_page + 1) % len(pages)

                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)
                        except asyncio.TimeoutError:
                            break

                    await message.clear_reactions()







    @ransomware.command()
    async def recent(self, ctx):
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
                        embed.add_field(name="Industry of service", value=item['activity'], inline=True)
                    if 'country' in item:
                        embed.add_field(name="Country of business", value=item['country'], inline=True)
                    
                    # Convert datetime string to timestamp
                    if 'published' in item:
                        published_timestamp = int(datetime.datetime.strptime(item['published'], "%Y-%m-%d %H:%M:%S.%f").timestamp())
                        embed.add_field(name="Published by hackers", value=f"**<t:{published_timestamp}:R>**", inline=True)
                    if 'discovered' in item:
                        discovered_timestamp = int(datetime.datetime.strptime(item['discovered'], "%Y-%m-%d %H:%M:%S.%f").timestamp())
                        embed.add_field(name="Discovered by indexer", value=f"**<t:{discovered_timestamp}:R>**", inline=True)
                    if 'group_name' in item:
                        embed.add_field(name="Ransom group", value=f"`{item['group_name']}`", inline=True)
                    if 'website' in item and item['website'] and item['website'].strip():
                        embed.add_field(name="Website compromised", value=f"`{item['website']}`", inline=True)
                    
                    pages.append(embed)

                message = await ctx.send(embed=pages[0])

                # Add URL button if post_url is present
                view = discord.ui.View()
                if 'post_url' in data[0]:
                    button = discord.ui.Button(label="Read the leak post", url=data[0]['post_url'])
                    view.add_item(button)

                # Add URL button to search the group name on Google if group_name is present
                if 'group_name' in data[0]:
                    google_search_url = f"https://www.google.com/search?q={data[0]['group_name']}%20ransomware%20group"
                    google_button = discord.ui.Button(label="Search on web", url=google_search_url)
                    view.add_item(google_button)

                await message.edit(view=view)

                emojis = ['⬅️', '❌', '➡️']
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
