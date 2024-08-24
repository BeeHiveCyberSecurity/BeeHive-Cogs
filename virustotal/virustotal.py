import aiohttp #type: ignore
import asyncio
import discord #type: ignore
import matplotlib.pyplot as plt #type: ignore
from redbot.core import commands #type: ignore

class VirusTotal(commands.Cog):
    """VirusTotal file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.submission_history = {}

    @commands.group(name="virustotal", invoke_without_command=True)
    async def virustotal(self, ctx):
        """Group for VirusTotal related commands"""
        await ctx.send_help(ctx.command)


    @commands.bot_has_permissions(embed_links=True)
    @virustotal.command(name="scan", aliases=["vt"])
    async def scan(self, ctx, file_url: str = None):
        """Submit a file to VirusTotal for analysis"""
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if not vt_key.get("api_key"):
                embed = discord.Embed(title='Error: No VirusTotal API Key set', description="Your Red instance doesn't have an API key set for VirusTotal.\n\nUntil you add an API key using `[p]set api`, the VirusTotal API will refuse your requests and this cog won't work.", colour=discord.Colour(0xff4545))
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/cog.png")
                await ctx.send(embed=embed)
                return

            async with aiohttp.ClientSession() as session:
                try:
                    # Check if a file URL is provided or if there are attachments in the message or the referenced message
                    attachments = ctx.message.attachments
                    if ctx.message.reference and not attachments:
                        ref_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                        attachments = ref_message.attachments

                    if file_url:
                        async with session.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": vt_key["api_key"]}, data={"url": file_url}) as response:
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                            data = await response.json()
                            permalink = data.get("data", {}).get("id")
                            if permalink:
                                await ctx.send(f"Permalink: https://www.virustotal.com/gui/url/{permalink}")
                                await self.check_results(ctx, permalink, ctx.author.id, file_url, None)
                            else:
                                raise ValueError("No permalink found in the response.")
                    elif attachments:
                        attachment = attachments[0]
                        if attachment.size > 30 * 1024 * 1024:  # 30 MB limit
                            embed = discord.Embed(title='Error: File too large', description="The file you provided exceeds the 30MB size limit for analysis.", colour=discord.Colour(0xff4545))
                            await ctx.send(embed=embed)
                            return
                        async with session.get(attachment.url) as response:
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                            file_content = await response.read()
                            file_name = attachment.filename  # Get the file name from the attachment
                            embed = discord.Embed(title="File uploaded successfully", description="**Starting analysis...**\nThis could take a few minutes, the bot will mention you when your analysis is complete and results are available", colour=discord.Colour(0x2BBD8E))
                            await ctx.send(embed=embed)
                            async with session.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, data={"file": file_content}) as response:
                                if response.status != 200:
                                    raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                                data = await response.json()
                                analysis_id = data.get("data", {}).get("id")
                                if analysis_id:
                                    await self.check_results(ctx, analysis_id, ctx.author.id, attachment.url, file_name)
                                    # Delete the attachment message from the channel
                                    await ctx.message.delete()
                                else:
                                    raise ValueError("No analysis ID found in the response.")
                    else:
                        embed = discord.Embed(title='No file provided', description="The bot was unable to find content to submit for analysis!\nPlease provide one of the following when using this command:\n- URL file can be downloaded from\n- Drag-and-drop a file less than 30mb in size\n- Reply to a message containing a file", colour=discord.Colour(0xff4545))
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                        await ctx.send(embed=embed)
                except (aiohttp.ClientResponseError, ValueError) as e:
                    embed = discord.Embed(title='Failed to submit file', description=str(e), colour=discord.Colour(0xff4545))
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                    await ctx.send(embed=embed)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title='Request timed out', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour(0xff4545))
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                    await ctx.send(embed=embed)

    async def check_results(self, ctx, analysis_id, presid, file_url, file_name):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        headers = {"x-apikey": vt_key["api_key"]}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers) as response:
                    if response.status != 200:
                        raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                    data = await response.json()
                    attributes = data.get("data", {}).get("attributes", {})
                    while attributes.get("status") != "completed":
                        await asyncio.sleep(3)
                        async with session.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers) as response:
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                            data = await response.json()
                            attributes = data.get("data", {}).get("attributes", {})
                    
                    stats = attributes.get("stats", {})
                    malicious_count = stats.get("malicious", 0)
                    suspicious_count = stats.get("suspicious", 0)
                    undetected_count = stats.get("undetected", 0)
                    harmless_count = stats.get("harmless", 0)
                    failure_count = stats.get("failure", 0)
                    unsupported_count = stats.get("type-unsupported", 0)
                    meta = data.get("meta", {}).get("file_info", {})
                    sha256 = meta.get("sha256")
                    sha1 = meta.get("sha1")
                    md5 = meta.get("md5")

                    total_count = malicious_count + suspicious_count + undetected_count + harmless_count + failure_count + unsupported_count
                    noanswer_count = failure_count + unsupported_count
                    safe_count = harmless_count + undetected_count
                    percent = round((malicious_count / total_count) * 100, 2) if total_count > 0 else 0
                    if sha256 and sha1 and md5:
                        embed = discord.Embed()
                        content = f"||<@{presid}>||"
                        if malicious_count >= 11:
                            embed.title = "Analysis complete"
                            embed.description = f"**{int(percent)}% of security vendors rated this file dangerous!**\n\nYou should avoid this file completely, and delete it from your systems to ensure security."
                            embed.color = discord.Colour(0xff4545)
                            embed.set_footer(text=f"SHA1 | {sha1}")
                        elif 1 < malicious_count < 11:
                            embed.title = "Analysis complete"
                            embed.description = f"**{int(percent)}% of security vendors rated this file dangerous**\n\nWhile there are malicious ratings available for this file, there aren't many, so this could be a false positive. **You should investigate further.**"
                            embed.color = discord.Colour(0xff9144)
                            embed.set_footer(text=f"SHA1 | {sha1}")
                        else:
                            embed.title = "Analysis complete"
                            embed.color = discord.Colour(0x2BBD8E)
                            embed.description = "**No security vendors currently flag this file as malicious**\n\nYou should be safe to run and use it.\nCheck back on the results later to see if vendors change their minds - it happens"
                            embed.set_footer(text=f"{sha1}")
                        button = discord.ui.Button(label="View results", url=f"https://www.virustotal.com/gui/file/{sha256}", style=discord.ButtonStyle.url)
                        button2 = discord.ui.Button(label="Get a second opinion", url="https://discord.gg/6PbaH6AfvF", style=discord.ButtonStyle.url)
                        view = discord.ui.View()
                        view.add_item(button)
                        view.add_item(button2)
                        await ctx.send(content=content, embed=embed, view=view)
                        self.log_submission(ctx.author.id, f"`{file_name}` - **{malicious_count}/{total_count}** - [View results](https://www.virustotal.com/gui/file/{sha256})")
                    else:
                        raise ValueError("Required hash values not found in the analysis response.")
            except (aiohttp.ClientResponseError, ValueError) as e:
                embed = discord.Embed(title='Analysis failed', description=str(e), colour=discord.Colour.red())
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                await ctx.send(embed=embed)
            except asyncio.TimeoutError:
                embed = discord.Embed(title='Request timed out', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour.red())
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                await ctx.send(embed=embed)

    def log_submission(self, user_id, summary):
        if user_id not in self.submission_history:
            self.submission_history[user_id] = []
        self.submission_history[user_id].append(summary)

    @commands.command(name="submissionhistory", description="View your submission history", aliases=["sh"])
    async def submission_history(self, ctx):
        user_id = ctx.author.id
        if user_id in self.submission_history and self.submission_history[user_id]:
            history = "\n".join(self.submission_history[user_id])
            embed = discord.Embed(title="Your Submission History", description=history, colour=discord.Colour(0x2BBD8E))
        else:
            embed = discord.Embed(title="No Submission History", description="You have not submitted any files for analysis yet.", colour=discord.Colour(0xff4545))
        await ctx.send(embed=embed)


