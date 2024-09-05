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
                    for person in data["persons"][:25]:  # Limit to first 25 results
                        embed = discord.Embed(
                            title=f"{person.get('firstName', 'Unknown')} {person.get('lastName', 'Unknown')}",
                            color=discord.Color.red()
                        )
                        if person.get('caseNumber'):
                            embed.add_field(name="Case Number", value=person.get('caseNumber'), inline=False)
                        if person.get('orgPrefix'):
                            embed.add_field(name="Organization Prefix", value=person.get('orgPrefix'), inline=False)
                        if person.get('orgName'):
                            embed.add_field(name="Organization Name", value=person.get('orgName'), inline=False)
                        if person.get('isChild') is not None:
                            is_child_value = "Yes" if person.get('isChild') else "No"
                            embed.add_field(name="Is Child", value=is_child_value, inline=False)
                        if person.get('seqNumber'):
                            embed.add_field(name="Sequence Number", value=person.get('seqNumber'), inline=False)
                        if person.get('langId'):
                            embed.add_field(name="Language ID", value=person.get('langId'), inline=False)
                        if person.get('firstName'):
                            embed.add_field(name="First Name", value=person.get('firstName'), inline=False)
                        if person.get('lastName'):
                            embed.add_field(name="Last Name", value=person.get('lastName'), inline=False)
                        if person.get('middleName'):
                            embed.add_field(name="Middle Name", value=person.get('middleName'), inline=False)
                        if person.get('missingCity'):
                            embed.add_field(name="Missing City", value=person.get('missingCity'), inline=False)
                        if person.get('missingCounty'):
                            embed.add_field(name="Missing County", value=person.get('missingCounty'), inline=False)
                        if person.get('missingState'):
                            embed.add_field(name="Missing State", value=person.get('missingState'), inline=False)
                        if person.get('missingCountry'):
                            embed.add_field(name="Missing Country", value=person.get('missingCountry'), inline=False)
                        if person.get('missingDate'):
                            embed.add_field(name="Missing Date", value=person.get('missingDate'), inline=False)
                        if person.get('age'):
                            embed.add_field(name="Age", value=person.get('age'), inline=False)
                        if person.get('approxAge'):
                            embed.add_field(name="Approximate Age", value=person.get('approxAge'), inline=False)
                        if person.get('hasThumbnail') is not None:
                            embed.add_field(name="Has Thumbnail", value=str(person.get('hasThumbnail')), inline=False)
                        if person.get('hasPoster') is not None:
                            embed.add_field(name="Has Poster", value=str(person.get('hasPoster')), inline=False)
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

