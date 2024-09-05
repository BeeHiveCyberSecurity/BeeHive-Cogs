import discord
from redbot.core import commands
import aiohttp
import asyncio
import json

class MissingKids(commands.Cog):
    """Cog to interact with the National Center for Missing and Exploited Children"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def ncmec(self, ctx):
        """Primary command group"""
        pass
    
    @ncmec.command()
    async def recent(self, ctx):
        """Fetch information about recently missing children."""
        url = "https://api.missingkids.org/missingkids/servlet/JSONDataServlet?action=publicSearch&goToPage=1"
        headers = {"Accept": "application/json"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        await ctx.send("Failed to fetch data from the MissingKids API.")
                        return

                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        text_data = await response.text()
                        try:
                            data = json.loads(text_data)
                        except json.JSONDecodeError:
                            await ctx.send("Failed to parse the response from the MissingKids API.")
                            return

                    if not data.get("persons"):
                        await ctx.send("No recently missing children found.")
                        return

                    embeds = []
                    for person in data["persons"][:10]:  # Limit to first 10 results
                        embed = discord.Embed(
                            title=f"{person.get('firstName', 'Unknown')} {person.get('lastName', 'Unknown')}",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Age", value=person.get('age', 'Unknown'), inline=False)
                        embed.add_field(name="Missing Since", value=person.get('missingDate', 'Unknown'), inline=False)
                        embed.add_field(name="Location", value=f"{person.get('missingCity', 'Unknown')}, {person.get('missingState', 'Unknown')}", inline=False)
                        embed.add_field(name="Case Number", value=person.get('caseNumber', 'Unknown'), inline=False)
                        image_url = person.get('thumbnailURL')
                        if image_url:
                            embed.set_thumbnail(url=f"https://api.missingkids.org{image_url}")
                        embeds.append(embed)

                    message = await ctx.send(embed=embeds[0])
                    await message.add_reaction("⬅️")
                    await message.add_reaction("❌")
                    await message.add_reaction("➡️")
                    
                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

                    i = 0
                    while True:
                        try:
                            reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
                            if str(reaction.emoji) == "➡️":
                                i += 1
                                if i >= len(embeds):
                                    i = 0
                                await message.edit(embed=embeds[i])
                            elif str(reaction.emoji) == "⬅️":
                                i -= 1
                                if i < 0:
                                    i = len(embeds) - 1
                                await message.edit(embed=embeds[i])
                            elif str(reaction.emoji) == "❌":
                                await message.delete()
                                break
                            await message.remove_reaction(reaction, user)
                        except asyncio.TimeoutError:
                            break
            except aiohttp.ClientError as e:
                await ctx.send(f"An error occurred while trying to fetch data: {str(e)}")
            except Exception as e:
                await ctx.send(f"An unexpected error occurred: {str(e)}")

