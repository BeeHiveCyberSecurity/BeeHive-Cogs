import discord #type: ignore
from redbot.core import commands, Config #type: ignore
import aiohttp #type: ignore
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
        self.war_activity_data = []
        self.current_page = 0
        self.bot.loop.create_task(self.check_and_send_alerts_loop())

    @commands.group(name="ukraine")
    async def ukraine(self, ctx):
        """Fetch information about the current conflict in Ukraine"""

    @ukraine.command(name="recent", description="Fetch and display recent war activity.")
    async def recent(self, ctx):
        """Show recent conflict activity"""
        headers = {
            "User-Agent": "Привіт від BeeHive, слава Україні! (Discord bot)"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(self.war_activity_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.war_activity_data = data.get("war_activity_posts", [])
                    else:
                        self.war_activity_data = []
            except aiohttp.ClientError:
                self.war_activity_data = []

        if not self.war_activity_data:
            await ctx.send("No recent war activity found.")
            return

        embed = self.create_embed(self.current_page)
        message = await ctx.send(embed=embed)
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "⬅️":
                    self.current_page = max(self.current_page - 1, 0)
                elif str(reaction.emoji) == "➡️":
                    self.current_page = min(self.current_page + 1, len(self.war_activity_data) - 1)

                embed = self.create_embed(self.current_page)
                await message.edit(embed=embed)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
            except discord.NotFound:
                break  # Exit the loop if the message is deleted
            except discord.Forbidden:
                break  # Exit the loop if the bot cannot remove reactions

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
                            self.war_activity_data = new_posts
                            new_last_alert_id = max(post["i"] for post in new_posts)
                            await self.config.guild_from_id(guild_id).last_alert_id.set(new_last_alert_id)
                            await self.send_alerts(guild_id, new_posts)
                        else:
                            self.war_activity_data = []
                    else:
                        self.war_activity_data = []
            except aiohttp.ClientError:
                self.war_activity_data = []

    async def send_alerts(self, guild_id, new_posts):
        alert_channel_id = await self.config.guild_from_id(guild_id).alert_channel_id()
        if alert_channel_id:
            channel = self.bot.get_channel(alert_channel_id)
            if channel:
                last_alert_id = await self.config.guild_from_id(guild_id).last_alert_id()
                for post in new_posts:
                    if post["i"] > last_alert_id:
                        embed = self.create_embed_from_post(post)
                        await channel.send(embed=embed)
                        await self.config.guild_from_id(guild_id).last_alert_id.set(post["i"])

    async def check_and_send_alerts_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                await self.fetch_war_activity(guild.id)
                if self.war_activity_data:
                    await self.send_alerts(guild.id, self.war_activity_data)
            await asyncio.sleep(120)  # Check every 2 minutes

    def create_embed(self, page):
        if not self.war_activity_data:
            return discord.Embed(
                title="Recent war activity",
                description="No data available.",
                colour=0xfffffe
            )
        post = self.war_activity_data[page]
        return self.create_embed_from_post(post)

    def create_embed_from_post(self, post):
        description_without_emoji = ''.join(char for char in post["me"] if char.isalnum() or char.isspace() or char in '.,!?')
        embed = discord.Embed(
            title="Recent war activity",
            description=description_without_emoji,
            colour=0xfffffe
        )
        embed.add_field(name="Source", value=post["su"], inline=False)
        embed.set_footer(text=f"Intel report")
        return embed
