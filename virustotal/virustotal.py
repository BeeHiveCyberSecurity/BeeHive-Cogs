import aiohttp #type: ignore
import asyncio
import discord #type: ignore
from redbot.core import commands #type: ignore

class VirusTotal(commands.Cog):
    """VirusTotal file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="virustotal", description="Submit a file for analysis via VirusTotal", aliases=["vt"])
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if not vt_key.get("api_key"):
                embed = discord.Embed(title='Error: No VirusTotal API Key set', description="Your Red instance doesn't have an API key set for VirusTotal.\n\nUntil you add an API key using `[p]set api`, the VirusTotal API will refuse your requests and this cog won't work.", colour=discord.Colour.red())
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                await ctx.send(embed=embed)
                return

            async with aiohttp.ClientSession() as session:
                try:
                    if file_url:
                        async with session.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": vt_key["api_key"]}, data={"url": file_url}) as response:
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                            data = await response.json()
                            permalink = data.get("data", {}).get("id")
                            if permalink:
                                await ctx.send(f"Permalink: https://www.virustotal.com/gui/url/{permalink}")
                                await self.check_results(ctx, permalink, ctx.author.id)
                            else:
                                raise ValueError("No permalink found in the response.")
                    elif ctx.message.attachments:
                        attachment = ctx.message.attachments[0]
                        async with session.get(attachment.url) as response:
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                            file_content = await response.read()
                            async with session.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, data={"file": file_content}) as response:
                                if response.status != 200:
                                    raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                                data = await response.json()
                                analysis_id = data.get("data", {}).get("id")
                                if analysis_id:
                                    await self.check_results(ctx, analysis_id, ctx.author.id)
                                else:
                                    raise ValueError("No analysis ID found in the response.")
                    else:
                        embed = discord.Embed(title='Error: No file provided', description="The bot was unable to find content to submit for analysis!\nPlease provide one of the following when using this command:\n- URL file can be downloaded from\n- Drag-and-drop a file less than 25mb in size", colour=discord.Colour.red())
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                        await ctx.send(embed=embed)
                except (aiohttp.ClientResponseError, ValueError) as e:
                    embed = discord.Embed(title='Error: Failed to submit file', description=str(e), colour=discord.Colour.red())
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title='Error: Request Timeout', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour.red())
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)

    async def check_results(self, ctx, analysis_id, presid):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        headers = {"x-apikey": vt_key["api_key"]}

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers) as response:
                        if response.status != 200:
                            raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                        data = await response.json()
                        attributes = data.get("data", {}).get("attributes", {})
                        if attributes.get("status") == "completed":
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
                                content = f"||<@{presid}>||"
                                if malicious_count >= 11:
                                    embed.title = "That file looks malicious!"
                                    embed.description = "You should avoid running, using, or handling the file out of an abundance of caution."
                                    embed.color = discord.Colour.red()
                                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                                elif 1 < malicious_count < 11:
                                    embed.title = "That file looks suspicious!"
                                    embed.description = "This file might be harmful. Exercise caution and consider further analysis."
                                    embed.color = discord.Colour.orange()
                                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-outline.png")
                                else:
                                    embed.title = "That file looks safe!"
                                    embed.color = discord.Colour.green()
                                    embed.description = "You should be safe to use this file.\nWant a [second opinion?](https://discord.gg/6PbaH6AfvF)"
                                    embed.add_field(name="Overall verdict", value="Clean", inline=False)
                                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                                total_count = malicious_count + suspicious_count + undetected_count + harmless_count + failure_count + unsupported_count
                                noanswer_count = failure_count + unsupported_count
                                safe_count = harmless_count + undetected_count
                                percent = round((malicious_count / total_count) * 100, 2) if total_count > 0 else 0
                                embed.add_field(name="Analysis results", value=f"**{percent}%** of security vendors rated this file dangerous!\n- **{malicious_count}** malicious\n- **{suspicious_count}** suspicious\n- **{safe_count}** detected no threats\n- **{noanswer_count}** engines couldn't check this file.", inline=False)
                                await ctx.send(content, embed=embed)
                                break
                            else:
                                raise ValueError("SHA256 value not found in the analysis response.")
                        else:
                            await asyncio.sleep(3)
                except (aiohttp.ClientResponseError, ValueError) as e:
                    embed = discord.Embed(title='Error: Analysis Failed', description=str(e), colour=discord.Colour.red())
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)
                    break
                except asyncio.TimeoutError:
                    embed = discord.Embed(title='Error: Request Timeout', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour.red())
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)
                    break
