import discord
from discord.ext import commands, tasks
import aiohttp

class WarActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.war_activity_url = "https://api.alerts.in.ua/v3/war_activity_posts/recent.json"
        self.war_activity_data = []
        self.current_page = 0

    @commands.command(name="waractivity", description="Fetch and display recent war activity.")
    async def waractivity(self, ctx):
        await self.fetch_war_activity()
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

    async def fetch_war_activity(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.war_activity_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.war_activity_data = data.get("war_activity_posts", [])

    def create_embed(self, page):
        post = self.war_activity_data[page]
        embed = discord.Embed(
            title="Recent War Activity",
            description=post["me"],
            colour=discord.Colour.red()
        )
        embed.add_field(name="Message", value=post["me"], inline=False)
        embed.add_field(name="Source", value=post["su"], inline=False)
        embed.set_footer(text=f"Page {page + 1} of {len(self.war_activity_data)}")
        return embed
