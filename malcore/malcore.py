import aiohttp #type: ignore
import asyncio
import re
import json
import discord # type: ignore
from redbot.core import commands # type: ignore
from redbot.core import app_commands # type: ignore

class Malcore(commands.Cog):
    """Malcore file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(name="urlcheck", description="Utilize Malcore's /urlcheck endpoint to scan a URL")
    async def urlcheck(self, ctx, url: str):
        mcore_key = await self.bot.get_shared_api_tokens("malcore")
        if mcore_key.get("api_key") is None:
            await ctx.send("The Malcore API key has not been set.")
        if url == "":
            await ctx.send("Please define a URL!")
        if "http" not in url and "https" not in url:
            await ctx.send("Please provide a valid URL!")
        headers = {
            "apiKey": mcore_key["api_key"]
        }
        data = {
            "url": url
        }
        try:
            async with ctx.typing():
                async with aiohttp.ClientSession() as session:
                    async with session.post('https://api.malcore.io/api/urlcheck', headers=headers, data=data, timeout=5) as r:
                        res = await r.text()
                        json_data = json.loads(res)
                        threat_level = json_data.get("data", {}).get("data", {}).get("threat_level")
                        embed = discord.Embed(url=f"{url}")
                        if threat_level and "SAFE" in threat_level:
                            embed.title = f"That URL looks safe"
                            embed.color = 0x2BBD8E  # Green color
                            embed.description = f"Malcore did not detect any threats associated with {url}"
                            embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                        else:
                            embed.title = f"This URL looks malicious!"
                            embed.description = f"Malcore says {url} is malicious!\n\nFor your own safety, please don't click it."
                            embed.color = 0xFF4545  # Red color
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                        await ctx.send(embed=embed)
        except (json.JSONDecodeError, aiohttp.ClientError, asyncio.TimeoutError):
            await ctx.send(f"Invalid JSON response from Malcore API or request timed out.")


    @commands.command()
    async def filecheck(self, ctx):
        mcore_key = await self.bot.get_shared_api_tokens("malcore")
        if mcore_key.get("api_key") is None:
            await ctx.send("The Malcore API key has not been set.")
        if ctx.message.attachments == "":
            await ctx.send("Please attach a file!")

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url, timeout=5) as response:
                        if response.status != 200:
                            embed = discord.Embed(title='Error: Failed to save file to memory', description=f"The bot was unable to submit that file to VirusTotal for analysis because the file download failed.", colour=16729413,)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                            return await ctx.send(embed=embed)
                        file_content = await response.read()
            except asyncio.TimeoutError:
                await ctx.send("File download timed out.")
                return

            headers = {
                "apiKey": mcore_key["api_key"],
                "X-No-Poll": False
            }
            try:
                async with ctx.typing():
                    async with aiohttp.ClientSession() as session:
                        form_data = aiohttp.FormData()
                        form_data.add_field('filename', file_content, filename='1')
                        async with session.post('https://api.malcore.io/api/upload', headers=headers, data=form_data, timeout=5) as r:
                            res = await r.text()
                            json_data = json.loads(res)
                            async with session.post('https://paste.org/', data={'text': json_data}, timeout=5) as r2:
                                paste_url = str(r2.url)
                                await ctx.send(f"Uploaded to Paste.org: {paste_url}")

            except (json.JSONDecodeError, aiohttp.ClientError, asyncio.TimeoutError):
                await ctx.send(f"Invalid JSON response from Malcore API or request timed out.")
        else:
            await ctx.send("Please attach a file!")