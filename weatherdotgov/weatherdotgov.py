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
                terms = [term for term in terms if term.get("term") and search_term.lower() in term.get("term", "").lower()]

            if not terms:
                await ctx.send(f"No glossary terms found for '{search_term}'.")
                return

            def html_to_markdown(html):
                """Convert HTML to Markdown"""
                replacements = {
                    "<b>": "**", "</b>": "**",
                    "<i>": "*", "</i>": "*",
                    "<strong>": "**", "</strong>": "**",
                    "<em>": "*", "</em>": "*",
                    "<br>": "\n", "<br/>": "\n", "<br />": "\n",
                    "<p>": "\n", "</p>": "\n",
                    "<ul>": "\n", "</ul>": "\n",
                    "<li>": "- ", "</li>": "\n",
                    "<h1>": "# ", "</h1>": "\n",
                    "<h2>": "## ", "</h2>": "\n",
                    "<h3>": "### ", "</h3>": "\n",
                    "<h4>": "#### ", "</h4>": "\n",
                    "<h5>": "##### ", "</h5>": "\n",
                    "<h6>": "###### ", "</h6>": "\n",
                }
                for html_tag, markdown in replacements.items():
                    html = html.replace(html_tag, markdown)
                return html

            pages = []
            for term in terms:
                word = term.get("term", "No title")
                description = term.get("definition", "No description")
                if word is None or description is None:  # Ignore terms or descriptions that are "null"
                    continue
                if not description:  # Ensure description is not empty
                    description = "No description available."
                description = html_to_markdown(description)
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

    @weather.command(name="activealerts")
    async def activealerts(self, ctx):
        """Fetches the counts of active alerts from weather.gov and displays them in an embed."""
        url = "https://api.weather.gov/alerts/active/count"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch active alerts.")
                    return
                data = await response.json()
                    
        pages = []

        # Page 1: total, land, marine
        embed1 = discord.Embed(title="Active Weather Alerts - Summary", color=0x1E90FF)
        for key in ["total", "land", "marine"]:
            if key in data:
                embed1.add_field(name=key, value=data[key], inline=False)
        pages.append(embed1)

        # Page 2: regions
        embed2 = discord.Embed(title="Active Weather Alerts - Regions", color=0x1E90FF)
        if "regions" in data:
            embed2.add_field(name="regions", value=data["regions"], inline=False)
        pages.append(embed2)

        # Page 3 and beyond: areas
        if "areas" in data:
            states = list(data["areas"].items())
            for i in range(0, len(states), 25):
                embed = discord.Embed(title="Active Weather Alerts - Areas", color=0x1E90FF)
                for state, count in states[i:i+25]:
                    embed.add_field(name=state, value=count, inline=True)
                pages.append(embed)

        if not pages:
            await ctx.send("No valid alert data found.")
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




