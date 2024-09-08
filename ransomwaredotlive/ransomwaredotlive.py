import discord #type: ignore
from redbot.core import commands #type: ignore
import aiohttp #type: ignore
import asyncio
import datetime
from discord.ext import tasks #type: ignore

class RansomwareDotLive(commands.Cog):
    """Interact with the ransomware.live API"""

    def __init__(self, bot):
        self.bot = bot
        self.alert_channel_id = None
        self.alert_role_id = None
        self.last_checked = datetime.datetime.utcnow()
        self.check_recent_victims.start()

    def cog_unload(self):
        self.check_recent_victims.cancel()

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
                        embed.add_field(name="Ransom group", value=f"`{item['group_name']}`", inline=True)
                    if 'website' in item and item['website'].strip():
                        embed.add_field(name="Website compromised", value=f"`{item['website']}`", inline=True)
                    
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
        if self.alert_channel_id is None:
            return

        channel = self.bot.get_channel(self.alert_channel_id)
        if channel is None:
            return

        role_mention = f"<@&{self.alert_role_id}>" if self.alert_role_id else ""

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
                embed.add_field(name="Ransom group", value=f"`{item['group_name']}`", inline=True)
            if 'website' in item and item['website'].strip():
                embed.add_field(name="Website compromised", value=f"`{item['website']}`", inline=True)
            
            await channel.send(content=role_mention, embed=embed)

    @tasks.loop(minutes=10)
    async def check_recent_victims(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.ransomware.live/recentvictims") as response:
                if response.status != 200:
                    return

                data = await response.json()
                new_victims = [item for item in data if datetime.datetime.strptime(item['published'], "%Y-%m-%d %H:%M:%S") > self.last_checked]

                if new_victims:
                    await self.send_alert(new_victims)
                    self.last_checked = datetime.datetime.utcnow()
