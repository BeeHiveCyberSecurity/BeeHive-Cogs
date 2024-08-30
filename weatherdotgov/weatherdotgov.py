import discord
from redbot.core import commands
import aiohttp
import asyncio

class Weather(commands.Cog):
    """Weather information from weather.gov"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def weather(self, ctx):
        """Weather command group"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand for weather.")

    @weather.command(name="glossary")
    async def glossary(self, ctx, *, search_term: str = None):
        """Fetch and display the weather glossary from weather.gov"""
        headers = {"Accept": "application/ld+json"}
        async with self.session.get("https://api.weather.gov/glossary", headers=headers) as response:
            if response.status != 200:
                await ctx.send("Failed to fetch the glossary. Please try again later.")
                return

            data = await response.json()
            terms = data.get("glossary", [])

            if not terms:
                await ctx.send("No glossary terms found.")
                return

            if search_term:
                terms = [term for term in terms if search_term.lower() in term.get("term", "").lower()]

            if not terms:
                await ctx.send(f"No glossary terms found for '{search_term}'.")
                return

            pages = []
            for term in terms:
                word = term.get("term", "No title")
                description = term.get("definition", "No description")
                if word is None or description is None:  # Ignore terms or descriptions that are "null"
                    continue
                if not description:  # Ensure description is not empty
                    description = "No description available."
                embed = discord.Embed(title=word, description=description, color=0x1E90FF)
                pages.append(embed)

            if not pages:
                await ctx.send("No valid glossary terms found.")
                return

            message = await ctx.send(embed=pages[0])
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            await message.add_reaction("❌")  # Add a close reaction

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

            i = 0
            reaction = None
            while True:
                if str(reaction) == "⬅️":
                    if i > 0:
                        i -= 1
                        await message.edit(embed=pages[i])
                elif str(reaction) == "➡️":
                    if i < len(pages) - 1:
                        i += 1
                        await message.edit(embed=pages[i])
                elif str(reaction) == "❌":
                    await message.delete()
                    break
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break




