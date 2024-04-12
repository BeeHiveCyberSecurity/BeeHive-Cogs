import requests
import asyncio
import discord
from redbot.core import commands
import time, json
import io

class VirusTotal(commands.Cog):
    """VirusTotal file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if vt_key.get("api_key") is None:
                vtkeyerror = discord.Embed(title='VirusTotal API Key not set', description="While VirusTotal offers users a free form of API access to the platform, you'll need to sign up for their platform first, then generate yourself an API Key for use with your Discord bot.\n\n### Getting started with VirusTotal API\nSign up for/sign into VirusTotal in your browser, then visit [this link](<https://www.virustotal.com/gui/my-apikey>) to locate your API key.\n\n### Setting your API key on your RedBot\nRun the command `[p]set api`, then complete the modal according to the image below. Once you save, your VirusTotal key will be ready for use!", colour=16729413,)
                vtkeyerror.set_image(url='https://i.imgur.com/Df2O98t.png')
                vtkeyerror.set_thumbnail(url='https://www.beehive.systems/hubfs/Icon%20Packs/Red/alert-circle-outline.png')
                vtkeyerror.set_author(name='Error')
                return await ctx.send(embed=vtkeyerror)
            else:
                if file_url:
                    response = requests.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": vt_key["api_key"]}, data={"url": file_url})
                    data = response.json()
                    if "permalink" in data:
                        permalink = data["permalink"]
                        await ctx.send(f"Permalink: {permalink.split('-')[1]}")
                        await self.check_results(ctx, permalink.split('-')[1])
                    else:
                        await ctx.send("Failed to submit the file for analysis.")
                elif ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    response = requests.get(attachment.url)
                    if response.status_code != 200:
                        return await ctx.send("Failed to download the attached file.")
                    file_content = response.content
                    response = requests.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, files={"file": file_content})
                    data = response.json()
                    analysis = data['data']['id']
                    await self.check_results(ctx, analysis, ctx.author.id)
                else:
                    await ctx.send("No file URL or attachment provided.")

    async def check_results(self, ctx, analysis_id, presid):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        headers = {"x-apikey": vt_key["api_key"]}
        
        while True:
            response = requests.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers)
            data = response.json()
            
            if "data" in data:
                attributes = data["data"].get("attributes")
                if attributes and attributes.get("status") == "completed":
                    stats = attributes.get("stats", {})
                    malicious_count = stats.get("malicious", 0)
                    suspicious_count = stats.get("suspicious", 0)
                    undetected_count = stats.get("undetected", 0)
                    harmless_count = stats.get("harmless", 0)
                    failure_count = stats.get("failure", 0)
                    unsupported_count = stats.get("type-unsupported", 0)
                    meta = data.get("meta", {}).get("file_info", {}).get("sha256")
                    
                    if meta:
                        embed = discord.Embed(title="File Analysis Completed", url=f"https://www.virustotal.com/gui/file/{meta}")
                        if malicious_count > 0:
                            content = f"||<@{presid}>||"
                            embed.description = f"VirusTotal analysis indicates this file could be malicious!"
                            embed.color = 0xFF4545  # Red color
                            embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/SPQpi1FTkADM8XzV0UQQ1eHe_EShYovjwHzX8YnjNkI/https/www.beehive.systems/hubfs/Icon%2520Packs/Red/warning-outline.png?format=webp&quality=lossless&width=910&height=910")
                        else:
                            content = f"||<@{presid}>||"
                            embed.color = 0x2BBD8E  # Green color
                            embed.description = f"VirusTotal analysis indicates this file is safe to use!"
                            embed.add_field(name="Status", value="Safe", inline=False)
                            embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/emlj4WYJyGGJaChkQdaMHt5bdsnE9pJUF5Qqgml4T5g/%3Fformat%3Dwebp%26quality%3Dlossless%26width%3D910%26height%3D910/https/images-ext-1.discordapp.net/external/OmwDVUJYkMMUoU_0CFX9rI2qpJ-mg_oMDpVkrrym0HY/https/www.beehive.systems/hubfs/Icon%252520Packs/Green/checkmark-circle-outline.png?format=webp&quality=lossless")
                        
                        total_count = malicious_count + suspicious_count + undetected_count + harmless_count + failure_count + unsupported_count
                        percentpre = malicious_count / total_count if total_count > 0 else 0
                        percent = round(percentpre * 100, 2)
                        embed.add_field(name="Analysis Results", value=f"**{percent}% of security vendors rated this file dangerous!**\n({malicious_count} malicious, {undetected_count} undetected)", inline=False)

                        await ctx.send(content, embed=embed)
                        break
                    else:
                        await ctx.send("Error: SHA256 value not found in the analysis response.")
                        break
            else:
                await ctx.send("Error: Analysis ID not found or analysis not completed yet.")
                break
            
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                pass
            
            await asyncio.sleep(3)