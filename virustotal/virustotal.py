import requests
import asyncio
import discord
from redbot.core import commands

class VirusTotal(commands.Cog):
    """Virus Total Inspection"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if vt_key.get("api_key") is None:
                return await ctx.send("The Virus Total API key has not been set.")
            else:
                if file_url:
                    response = requests.post("https://www.virustotal.com/vtapi/v2/url/scan", params={"apikey": vt_key["api_key"]}, data={"url": file_url})
                    data = response.json()
                    if "permalink" in data:
                        permalink = data["permalink"]
                        await ctx.send(f"Permalink: {permalink.split('-')[1]}")
                        await self.check_results(ctx, permalink)
                    else:
                        await ctx.send("Failed to submit the file for analysis.")
                elif ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    response = requests.get(attachment.url)
                    if response.status_code != 200:
                        return await ctx.send("Failed to download the attached file.")
                    file_content = response.content
                    response = requests.post("https://www.virustotal.com/vtapi/v2/file/scan", params={"apikey": vt_key["api_key"]}, files={"file": file_content})
                    data = response.json()
                    if "permalink" in data:
                        permalink = data["permalink"]
                        await ctx.send(f"Permalink: {permalink.split('-')[1]}")
                        await self.check_results(ctx, permalink)
                    else:
                        await ctx.send("Failed to submit the file for analysis.")
                else:
                    await ctx.send("No file URL or attachment provided.")

    async def check_results(self, ctx, permalink):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        while True:
            response = requests.get(permalink, params={"apikey": vt_key["api_key"]})
            data = response.json()
            if "positives" in data:
                positives = data["positives"]
                total = data["total"]
                if positives > 0:
                    await ctx.send(f"The file has been detected as malicious by {positives}/{total} scanners.")
                else:
                    await ctx.send("The file is not detected as malicious by any scanner.")
                break
            else:
                await asyncio.sleep(3)