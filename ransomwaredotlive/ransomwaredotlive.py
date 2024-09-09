import discord #type: ignore
from redbot.core import commands #type: ignore
import aiohttp #type: ignore
import asyncio
import datetime
from discord.ext import tasks #type: ignore

class RansomwareDotLive(commands.Cog):
    """Interact with the ransomware.live API"""

    __version__ = "**1.0.0.8**"
    __last_updated__ = "**September 9th, 2024**"

    def __init__(self, bot):
        self.bot = bot
        self.alert_channel_id = None
        self.alert_role_id = None
        self.last_checked_name = None
        self.check_recent_victims.start()

    def cog_unload(self):
        self.check_recent_victims.cancel()

    @tasks.loop(minutes=2)
    async def check_recent_victims(self):
        headers = {
            "User-Agent": "DiscordBot (BeeHive-Cogs, ransomwaredotlive)"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get("https://api.ransomware.live/recentvictims") as response:
                if response.status != 200:
                    return

                data = await response.json()
                if self.last_checked_name:
                    new_victims = []
                    for item in data:
                        if item['name'] == self.last_checked_name:
                            break
                        new_victims.append(item)
                else:
                    new_victims = data

                if new_victims:
                    await self.send_alert(new_victims)
                    self.last_checked_name = new_victims[0]['name']  # Update last_checked_name only if there are new victims

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
                        # Transform HTML to markdown in the description
                        description = group['description'].replace('<br>', '\n').replace('<b>', '**').replace('</b>', '**').replace('<BR>', '\n')
                        embed.description = description
                    
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
                    await message.add_reaction("❌")  # Add close reaction

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

                    current_page = 0
                    while True:
                        try:
                            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                            if str(reaction.emoji) == "⬅️":
                                current_page = (current_page - 1) % len(pages)
                            elif str(reaction.emoji) == "➡️":
                                current_page = (current_page + 1) % len(pages)
                            elif str(reaction.emoji) == "❌":
                                await message.delete()
                                break

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
                        try:
                            published_timestamp = int(datetime.datetime.strptime(item['published'], "%Y-%m-%d %H:%M:%S.%f").timestamp())
                            embed.add_field(name="Published by hackers", value=f"**<t:{published_timestamp}:R>**", inline=True)
                        except ValueError:
                            pass
                    if 'discovered' in item:
                        try:
                            discovered_timestamp = int(datetime.datetime.strptime(item['discovered'], "%Y-%m-%d %H:%M:%S.%f").timestamp())
                            embed.add_field(name="Discovered by indexer", value=f"**<t:{discovered_timestamp}:R>**", inline=True)
                        except ValueError:
                            pass
                    if 'group_name' in item:
                        embed.add_field(name="Ransom group", value=f"`{item['group_name']}`", inline=True)
                    if 'website' in item and item['website'].strip():
                        embed.add_field(name="Website compromised", value=f"`{item['website']}`", inline=True)
                    if 'screenshot' in item and item['screenshot'].strip():
                        embed.set_image(url=item['screenshot'])
                    if 'infostealer' in item:
                        infostealer_info = item['infostealer']
                        if 'employees' in infostealer_info and infostealer_info.get('employees', 0) != 0:
                            embed.add_field(name="Employees with data stolen", value=infostealer_info.get('employees', 'N/A'), inline=True)
                        if 'thirdparties' in infostealer_info and infostealer_info.get('thirdparties', 0) != 0:
                            embed.add_field(name="Third parties with data stolen", value=infostealer_info.get('thirdparties', 'N/A'), inline=True)
                        if 'users' in infostealer_info and infostealer_info.get('users', 0) != 0:
                            embed.add_field(name="Users with data stolen", value=infostealer_info.get('users', 'N/A'), inline=True)
                    
                    pages.append(embed)

                message = await ctx.send(embed=pages[0])

                # Add URL button if post_url is present
                view = discord.ui.View()
                if 'post_url' in data[0] and data[0]['post_url'].strip():
                    button = discord.ui.Button(label="Read the leak post", url=data[0]['post_url'])
                    view.add_item(button)

                # Add URL button to search the group name on Google if group_name is present
                if 'group_name' in data[0] and data[0]['group_name'].strip():
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
    
    @ransomware.command()
    async def about(self, ctx):
        """Show the version and last updated date of this cog"""
        embed = discord.Embed(title="About this cog", color=0xfffffe)
        embed.add_field(name="Version", value=self.__version__)
        embed.add_field(name="Last updated", value=self.__last_updated__)
        await ctx.send(embed=embed)

    @commands.admin_or_permissions()
    @commands.group()
    async def ransomwareset(self, ctx):
        "Configure ransomware monitoring and alerting functionality"
        pass

    @commands.admin_or_permissions()
    @ransomwareset.command()
    async def alertchannel(self, ctx, channel: discord.TextChannel):
        """Set a channel for new ransomware victim alerts"""
        self.alert_channel_id = channel.id
        await ctx.send(f"Alerts channel set to {channel.mention}")

    @commands.admin_or_permissions()
    @ransomwareset.command()
    async def alertrole(self, ctx, role: discord.Role):
        """Set a role to be mentioned for new ransomware victim alerts"""
        self.alert_role_id = role.id
        await ctx.send(f"Alert role set to {role.mention}")

    async def send_alert(self, data):
        if not self.alert_channel_id:
            return

        channel = self.bot.get_channel(self.alert_channel_id)
        if channel is None:
            return

        role_mention = f"<@&{self.alert_role_id}>" if self.alert_role_id else ""

        for item in data:
            embed = discord.Embed(title=item.get("post_title", "No Title"), color=0xfffffe)
            embed.description = item.get('description', 'No Description')
            
            if 'activity' in item:
                embed.add_field(name="Industry of service", value=item['activity'], inline=True)
            if 'country' in item:
                embed.add_field(name="Country of business", value=item['country'], inline=True)
            
            # Convert datetime string to timestamp
            if 'published' in item:
                try:
                    published_timestamp = int(datetime.datetime.strptime(item['published'], "%Y-%m-%d %H:%M:%S").timestamp())
                    embed.add_field(name="Published by hackers", value=f"**<t:{published_timestamp}:R>**", inline=True)
                except ValueError:
                    pass
            if 'discovered' in item:
                try:
                    discovered_timestamp = int(datetime.datetime.strptime(item['discovered'], "%Y-%m-%d %H:%M:%S").timestamp())
                    embed.add_field(name="Discovered by indexer", value=f"**<t:{discovered_timestamp}:R>**", inline=True)
                except ValueError:
                    pass
            if 'group_name' in item:
                embed.add_field(name="Threat actor/group", value=f"`{item['group_name']}`", inline=True)
            if 'website' in item and item['website'].strip():
                embed.add_field(name="Website hit", value=f"`{item['website']}`", inline=True)
            
            await channel.send(content=role_mention, embed=embed)
