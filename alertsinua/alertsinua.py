import discord  # type: ignore
from redbot.core import commands, Config  # type: ignore
import aiohttp  # type: ignore
import asyncio

class WarActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "alert_channel_id": None,
            "last_alert_id": 0
        }
        self.config.register_guild(**default_guild)
        self.war_activity_url = "https://api.alerts.in.ua/v3/war_activity_posts/recent.json"
        self.bot.loop.create_task(self.check_and_send_alerts_loop())

    @commands.group(name="ukraine")
    async def ukraine(self, ctx):
        """Fetch information about the current conflict in Ukraine"""

    @ukraine.command(name="setchannel", description="Set the channel for war activity alerts.")
    @commands.has_permissions(manage_channels=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).alert_channel_id.set(channel.id)
        await ctx.send(f"Alert channel set to {channel.mention}")

    async def fetch_war_activity(self, guild_id):
        headers = {
            "User-Agent": "Привіт від BeeHive, слава Україні! (Discord bot)"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(self.war_activity_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        last_alert_id = await self.config.guild_from_id(guild_id).last_alert_id()
                        new_posts = [post for post in data.get("war_activity_posts", []) if post["i"] > last_alert_id]
                        if new_posts:
                            await self.send_alerts(guild_id, new_posts)
                            new_last_alert_id = max(post["i"] for post in new_posts)
                            await self.config.guild_from_id(guild_id).last_alert_id.set(new_last_alert_id)
                    else:
                        print(f"Failed to fetch war activity: HTTP {response.status}")
            except aiohttp.ClientError as e:
                print(f"Error fetching war activity: {e}")

    async def send_alerts(self, guild_id, new_posts):
        alert_channel_id = await self.config.guild_from_id(guild_id).alert_channel_id()
        if alert_channel_id:
            channel = self.bot.get_channel(alert_channel_id)
            if channel:
                for post in new_posts:
                    embed = self.create_embed_from_post(post)
                    try:
                        await channel.send(embed=embed)
                    except discord.HTTPException as e:
                        print(f"Failed to send alert: {e}")

    async def check_and_send_alerts_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                await self.fetch_war_activity(guild.id)
            await asyncio.sleep(120)  # Check every 2 minutes

    def create_embed_from_post(self, post):
        description_without_emoji = ''.join(char for char in post["me"] if char.isalnum() or char.isspace() or char in '.,!?')
        embed = discord.Embed(
            title="From the battlefield",
            description=description_without_emoji,
            colour=0xfffffe
        )
        embed.set_footer(text="✨ Machine translated from Ukrainian, accuracy may vary.")
        return embed

    @ukraine.command(name="recent")
    async def recent(self, ctx):
        """Shows all recent war activity in a scrollable embed."""
        guild_id = ctx.guild.id
        headers = {
            "User-Agent": "Привіт від BeeHive, слава Україні! (Discord bot)"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(self.war_activity_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get("war_activity_posts", [])
                        if posts:
                            embeds = [self.create_embed_from_post(post) for post in posts]
                            message = await ctx.send(embed=embeds[0])
                            
                            if len(embeds) > 1:
                                await message.add_reaction("⬅️")
                                await message.add_reaction("➡️")
                                await message.add_reaction("❌")  # Add close reaction

                                def check(reaction, user):
                                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

                                i = 0
                                while True:
                                    try:
                                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                                        if str(reaction.emoji) == "➡️" and i < len(embeds) - 1:
                                            i += 1
                                            await message.edit(embed=embeds[i])
                                        elif str(reaction.emoji) == "⬅️" and i > 0:
                                            i -= 1
                                            await message.edit(embed=embeds[i])
                                        elif str(reaction.emoji) == "❌":
                                            await message.delete()
                                            break
                                        await message.remove_reaction(reaction, user)
                                    except asyncio.TimeoutError:
                                        break
                        else:
                            await ctx.send("No recent intelligence reports found.")
                    else:
                        await ctx.send(f"Failed to fetch intelligence: HTTP {response.status}")
            except aiohttp.ClientError as e:
                await ctx.send(f"Error occurred while fetching intelligence: {e}")

