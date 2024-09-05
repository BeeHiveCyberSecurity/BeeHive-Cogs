import discord
from redbot.core import commands
import aiohttp
import asyncio
import json
import datetime

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
                    for person in data["persons"][:25]:  # Limit to first 25 results
                        embed = discord.Embed(
                            title=f"{person.get('firstName', 'Unknown')} {person.get('middleName')} {person.get('lastName', 'Unknown')}",
                            color=0xfffffe
                        )
                        if person.get('caseNumber'):
                            embed.add_field(name="Case number", value=person.get('caseNumber'), inline=False)
                        if person.get('orgName'):
                            embed.add_field(name="Issuing organization", value=person.get('orgName'), inline=False)
                        if person.get('firstName'):
                            embed.add_field(name="First name", value=person.get('firstName'), inline=True)
                        if person.get('middleName'):
                            embed.add_field(name="Middle name", value=person.get('middleName'), inline=True)
                        if person.get('lastName'):
                            embed.add_field(name="Last name", value=person.get('lastName'), inline=True)
                        if person.get('age'):
                            embed.add_field(name="Age", value=person.get('age'), inline=False)
                        if person.get('approxAge'):
                            embed.add_field(name="Estimated age", value=person.get('approxAge'), inline=False)
                        if person.get('missingCity'):
                            embed.add_field(name="Missing city", value=person.get('missingCity').title(), inline=False)
                        if person.get('missingCounty'):
                            embed.add_field(name="Missing county", value=person.get('missingCounty').title(), inline=False)
                        if person.get('missingState'):
                            embed.add_field(name="Missing state", value=person.get('missingState').title(), inline=False)
                        if person.get('missingCountry'):
                            embed.add_field(name="Missing country", value=person.get('missingCountry').title(), inline=False)
                        if person.get('missingDate'):
                            missing_date = person.get('missingDate')
                            embed.add_field(
                                name="Missing Date", 
                                value=f"<t:{int(datetime.datetime.strptime(missing_date, '%Y-%m-%d').timestamp())}:F> (<t:{int(datetime.datetime.strptime(missing_date, '%Y-%m-%d').timestamp())}:R>)", 
                                inline=False
                            )
                        if person.get('caseType'):
                            embed.add_field(name="Case Type", value=person.get('caseType'), inline=False)
                        if person.get('posterTitle'):
                            embed.add_field(name="Poster Title", value=person.get('posterTitle'), inline=False)
                        if person.get('race'):
                            embed.add_field(name="Race", value=person.get('race'), inline=False)
                        thumbnail_url = person.get('thumbnailUrl')
                        if thumbnail_url:
                            embed.set_thumbnail(url=f"https://api.missingkids.org{thumbnail_url}")
#                        image_url = person.get('imageUrl')
#                        if image_url:
#                            embed.set_image(url=f"https://api.missingkids.org{image_url}")
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

