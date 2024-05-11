import time
import json
import io
import requests
import asyncio
import discord # type: ignore
from redbot.core import commands
from redbot.core import app_commands # type: ignore

class VirusTotal(commands.Cog):
    """VirusTotal file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="virustotal", description="Submit a file for analysis via VirusTotal", aliases=["vt"])
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if vt_key.get("api_key") is None:
                embed = discord.Embed(title='Error: No VirusTotal API Key set', description=f"Your Red instance doesn't have an API key set for VirusTotal.\n\nUntil you add an API key using `[p]set api`, the VirusTotal API will refuse your requests and this cog won't work.", colour=16729413,)
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                return await ctx.send(embed=embed)
            else:
                try:
                    if file_url:
                        response = requests.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": vt_key["api_key"]}, data={"url": file_url}, timeout=10)
                        data = response.json()
                        if "permalink" in data:
                            permalink = data["permalink"]
                            await ctx.send(f"Permalink: {permalink.split('-')[1]}")
                            await self.check_results(ctx, permalink.split('-')[1])
                        else:
                            embed = discord.Embed(title='Error: Failed to submit file', description=f"The bot was unable to submit that file to VirusTotal for analysis.", colour=16729413,)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                            await ctx.send(embed=embed)
                    elif ctx.message.attachments:
                        attachment = ctx.message.attachments[0]
                        response = requests.get(attachment.url, timeout=10)
                        if response.status_code != 200:
                            embed = discord.Embed(title='Error: Failed to save file to memory', description=f"The bot was unable to submit that file to VirusTotal for analysis because the file download failed.", colour=16729413,)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                            return await ctx.send(embed=embed)
                        file_content = response.content
                        response = requests.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, files={"file": file_content}, timeout=10)
                        data = response.json()
                        analysis = data['data']['id']
                        await self.check_results(ctx, analysis, ctx.author.id)
                    else:
                        embed = discord.Embed(title='Error: No file provided', description=f"The bot was unable to find content to submit for analysis!\nPlease provide one of the following when using this command\n- URL file can be downloaded from\n- Drag-and-drop a file less than 25mb in size", colour=16729413,)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                        await ctx.send(embed=embed)
                except requests.exceptions.Timeout:
                    embed = discord.Embed(title='Error: Request Timeout', description=f"The bot was unable to complete the request due to a timeout.", colour=16729413,)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)

    async def check_results(self, ctx, analysis_id, presid):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        headers = {"x-apikey": vt_key["api_key"]}
        
        while True:
            try:
                response = requests.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers, timeout=10)
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
                            embed = discord.Embed(url=f"https://www.virustotal.com/gui/file/{meta}")
                            if malicious_count > 0:
                                content = f"||<@{presid}>||"
                                embed.title = f"That file looks malicious!"
                                embed.description = f"You should avoid running, using, or handling the file out of an abundance of caution"
                                embed.color = 0xFF4545  # Red color
                                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                            else:
                                content = f"||<@{presid}>||"
                                embed.title = f"That file looks safe!"
                                embed.color = 0x2BBD8E  # Green color
                                embed.description = f"You should be safe to use this file.\nWant a [second opinion?](<https://discord.gg/6PbaH6AfvF>)"
                                embed.add_field(name="Overall verdict", value="Clean", inline=False)
                                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                            
                            total_count = malicious_count + suspicious_count + undetected_count + harmless_count + failure_count + unsupported_count
                            noanswer_count = failure_count + unsupported_count
                            safe_count = harmless_count + undetected_count
                            percentpre = malicious_count / total_count if total_count > 0 else 0
                            percent = round(percentpre * 100, 2)
                            embed.add_field(name="Analysis results", value=f"**{percent}%** of security vendors rated this file dangerous!\n- **{malicious_count}** malicious\n- **{suspicious_count}** suspicious\n- **{safe_count}** detected no threats\n- **{noanswer_count}** engines couldn't check this file.", inline=False)

                            await ctx.send(content, embed=embed)
                            break
                        else:
                            embed = discord.Embed(title='Error: SHA256 value not found in the analysis response', description=f"VirusTotal did not correctly match an Analysis ID with a file hash in the API response - try again, this is an odd error.", colour=16729413,)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                            await ctx.send(embed=embed)
                            break
                else:
                    await ctx.send("Error: Analysis ID not found or analysis not completed yet.")
                    break
            except requests.exceptions.Timeout:
                embed = discord.Embed(title='Error: Request Timeout', description=f"The bot was unable to complete the request due to a timeout.", colour=16729413,)
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                await ctx.send(embed=embed)
                break
            
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                pass
            
            await asyncio.sleep(3)
