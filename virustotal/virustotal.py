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
                    response = requests.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, json={"url": file_url})
                    data = response.json()
                    if "data" in data and "id" in data["data"]:
                        analysis_id = data["data"]["id"]
                        await ctx.send(f"Analysis ID: {analysis_id}")
                        await self.process_analysis(ctx, analysis_id)
                    else:
                        await ctx.send("Failed to submit the file for analysis.")
                        return
                elif ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    response = requests.get(attachment.url)
                    if response.status_code != 200:
                        return await ctx.send("Failed to download the attached file.")
                    file_content = response.content
                    response = requests.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, data=file_content)
                    data = response.json()
                    if "data" in data and "id" in data["data"]:
                        analysis_id = data["data"]["id"]
                        await ctx.send(f"Analysis ID: {analysis_id}")
                    else:
                        await ctx.send("Failed to submit the file for analysis. [fileupload]")
                        return
                else:
                    await ctx.send("No file URL or attachment provided.")

    async def process_analysis(self, ctx, analysis_id):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        while True:
            response = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers={"x-apikey": vt_key["api_key"]})
            analysis_data = response.json()
            # Check if analysis is completed
            if analysis_data["data"]["attributes"]["status"] == "completed":
                results = analysis_data["data"]["attributes"]["results"]
                embed_response = discord.Embed(title="VirusTotal Results", color=0x00FF00)
                for engine, result_data in results.items():
                    if result_data["result"]:
                        embed_response.add_field(name=engine, value=result_data["result"], inline=False)
                await ctx.send(embed=embed_response)
                break
            elif "errors" in analysis_data:
                await ctx.send("Failed to submit the file for analysis. [process_analysis]")
                break
            else:
                await asyncio.sleep(3)