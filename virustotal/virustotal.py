import aiohttp #type: ignore
import asyncio
import discord #type: ignore
from redbot.core import commands #type: ignore

class VirusTotal(commands.Cog):
    """VirusTotal file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.submission_history = {}
        self.auto_scan_enabled = False

    @commands.group(name="virustotal", invoke_without_command=True)
    async def virustotal(self, ctx):
        """Group for VirusTotal related commands"""
        await ctx.send_help(ctx.command)

    @virustotal.command(name="toggleautoscan")
    async def toggle_auto_scan(self, ctx):
        """Toggle automatic file scanning on or off"""
        self.auto_scan_enabled = not self.auto_scan_enabled
        status = "enabled" if self.auto_scan_enabled else "disabled"
        await ctx.send(f"Automatic file scanning has been {status}.")

    @virustotal.command(name="settings")
    async def settings(self, ctx):
        """Show current settings for VirusTotal"""
        status = "enabled" if self.auto_scan_enabled else "disabled"
        
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        api_key_status = "set" if vt_key.get("api_key") else "not set"
        
        version = "1.0.0"  # Example version, replace with actual version if available
        last_update = "August 24th, 2024"  # Example last update date, replace with actual date if available
        
        embed = discord.Embed(title="VirusTotal Settings", colour=discord.Colour(0x2BBD8E))
        embed.add_field(name="Automatic File Scanning", value=status, inline=False)
        embed.add_field(name="API Key", value=api_key_status, inline=False)
        embed.add_field(name="Version", value=version, inline=False)
        embed.add_field(name="Last Updated", value=last_update, inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Automatically scan files if auto_scan is enabled"""
        if self.auto_scan_enabled and message.attachments:
            ctx = await self.bot.get_context(message)
            if ctx.valid:
                await self.silent_scan(ctx, message.attachments)
                
    async def silent_scan(self, ctx, attachments):
        """Scan files silently and alert only if they're malicious or suspicious"""
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        if not vt_key.get("api_key"):
            return  # No API key set, silently return

        async with aiohttp.ClientSession() as session:
            for attachment in attachments:
                if attachment.size > 30 * 1024 * 1024:  # 30 MB limit
                    continue  # Skip files that are too large

                async with session.get(attachment.url) as response:
                    if response.status != 200:
                        continue  # Skip files that can't be downloaded

                    file_content = await response.read()
                    file_name = attachment.filename

                    async with session.post(
                        "https://www.virustotal.com/api/v3/files",
                        headers={"x-apikey": vt_key["api_key"]},
                        data={"file": file_content},
                    ) as vt_response:
                        if vt_response.status != 200:
                            continue  # Skip files that can't be uploaded

                        data = await vt_response.json()
                        analysis_id = data.get("data", {}).get("id")
                        if not analysis_id:
                            continue  # Skip files without a valid analysis ID

                        # Check the analysis results
                        await asyncio.sleep(15)  # Wait for the analysis to complete
                        async with session.get(
                            f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                            headers={"x-apikey": vt_key["api_key"]},
                        ) as result_response:
                            if result_response.status != 200:
                                continue  # Skip files that can't be checked

                            result_data = await result_response.json()
                            stats = result_data.get("data", {}).get("attributes", {}).get("stats", {})
                            if stats.get("malicious", 0) > 0 or stats.get("suspicious", 0) > 0:
                                await ctx.send(f"Alert: The file {file_name} is flagged as malicious or suspicious.")

    @commands.bot_has_permissions(embed_links=True)
    @virustotal.command(name="scan", aliases=["vt"])
    async def scan(self, ctx, file_url: str = None):
        """Submit a file to VirusTotal for analysis"""
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if not vt_key.get("api_key"):
                if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                    embed = discord.Embed(title='Error: No VirusTotal API Key set', description="Your Red instance doesn't have an API key set for VirusTotal.\n\nUntil you add an API key using `[p]set api`, the VirusTotal API will refuse your requests and this cog won't work.", colour=discord.Colour(0xff4545))
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/cog.png")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Error: No VirusTotal API Key set. Your Red instance doesn't have an API key set for VirusTotal. Until you add an API key using `[p]set api`, the VirusTotal API will refuse your requests and this cog won't work.")
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
                            if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                                embed = discord.Embed(title='Error: File too large', description="The file you provided exceeds the 30MB size limit for analysis.", colour=discord.Colour(0xff4545))
                                await ctx.send(embed=embed)
                            else:
                                await ctx.send("Error: File too large. The file you provided exceeds the 30MB size limit for analysis.")
                            return
                        async with session.get(attachment.url) as response:
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                            file_content = await response.read()
                            file_name = attachment.filename  # Get the file name from the attachment
                            if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                                embed = discord.Embed(title="Starting analysis", description="This could take a few minutes, please be patient. You'll be mentioned when results are available.", colour=discord.Colour(0x2BBD8E))
                                await ctx.send(embed=embed)
                            else:
                                await ctx.send("Starting analysis. This could take a few minutes, please be patient. You'll be mentioned when results are available.")
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
                        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                            embed = discord.Embed(title='No file provided', description="The bot was unable to find content to submit for analysis!\nPlease provide one of the following when using this command:\n- URL file can be downloaded from\n- Drag-and-drop a file less than 30mb in size\n- Reply to a message containing a file", colour=discord.Colour(0xff4545))
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("No file provided. The bot was unable to find content to submit for analysis! Please provide one of the following when using this command:\n- URL file can be downloaded from\n- Drag-and-drop a file less than 30mb in size\n- Reply to a message containing a file")
                except (aiohttp.ClientResponseError, ValueError) as e:
                    if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                        embed = discord.Embed(title='Failed to submit file', description=str(e), colour=discord.Colour(0xff4545))
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"Failed to submit file: {str(e)}")
                except asyncio.TimeoutError:
                    if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                        embed = discord.Embed(title='Request timed out', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour(0xff4545))
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("Request timed out. The bot was unable to complete the request due to a timeout.")

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
                        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                            embed = discord.Embed()
                            content = f"||<@{presid}>||"
                            if malicious_count >= 11:
                                embed.title = "Analysis complete"
                                embed.description = f"**{int(percent)}%** of vendors rated this file dangerous! You should avoid this file completely, and delete it from your systems to ensure security."
                                embed.color = discord.Colour(0xff4545)
                                embed.set_footer(text=f"SHA1 | {sha1}")
                            elif 1 < malicious_count < 11:
                                embed.title = "Analysis complete"
                                embed.description = f"**{int(percent)}%** of vendors rated this file dangerous. While there are malicious ratings available for this file, there aren't many, so this could be a false positive. **You should investigate further before coming to a decision.**"
                                embed.color = discord.Colour(0xff9144)
                                embed.set_footer(text=f"SHA1 | {sha1}")
                            else:
                                embed.title = "Analysis complete"
                                embed.color = discord.Colour(0x2BBD8E)
                                embed.description = f"**{safe_count}** vendors say this file is malware-free"
                                embed.set_footer(text=f"{sha1}")
                            button = discord.ui.Button(label="View results on VirusTotal", url=f"https://www.virustotal.com/gui/file/{sha256}", style=discord.ButtonStyle.url)
                            button2 = discord.ui.Button(label="Get a second opinion", url="https://discord.gg/6PbaH6AfvF", style=discord.ButtonStyle.url)
                            view = discord.ui.View()
                            view.add_item(button)
                            view.add_item(button2)
                            await ctx.send(content=content, embed=embed, view=view)
                        else:
                            content = f"||<@{presid}>||"
                            if malicious_count >= 11:
                                await ctx.send(f"{content}\nAnalysis complete: **{int(percent)}%** of vendors rated this file dangerous! You should avoid this file completely, and delete it from your systems to ensure security.\nSHA1: {sha1}\nView results on VirusTotal: https://www.virustotal.com/gui/file/{sha256}\nGet a second opinion: https://discord.gg/6PbaH6AfvF")
                            elif 1 < malicious_count < 11:
                                await ctx.send(f"{content}\nAnalysis complete: **{int(percent)}%** of vendors rated this file dangerous. While there are malicious ratings available for this file, there aren't many, so this could be a false positive. **You should investigate further before coming to a decision.**\nSHA1: {sha1}\nView results on VirusTotal: https://www.virustotal.com/gui/file/{sha256}\nGet a second opinion: https://discord.gg/6PbaH6AfvF")
                            else:
                                await ctx.send(f"{content}\nAnalysis complete: **{safe_count}** vendors say this file is malware-free\nSHA1: {sha1}\nView results on VirusTotal: https://www.virustotal.com/gui/file/{sha256}\nGet a second opinion: https://discord.gg/6PbaH6AfvF")
                        self.log_submission(ctx.author.id, f"`{file_name}` - **{malicious_count}/{total_count}** - [View results](https://www.virustotal.com/gui/file/{sha256})")
                    else:
                        raise ValueError("Required hash values not found in the analysis response.")
            except (aiohttp.ClientResponseError, ValueError) as e:
                if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                    embed = discord.Embed(title='Analysis failed', description=str(e), colour=discord.Colour.red())
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Analysis failed: {str(e)}")
            except asyncio.TimeoutError:
                if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                    embed = discord.Embed(title='Request timed out', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour.red())
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Request timed out. The bot was unable to complete the request due to a timeout.")

    def log_submission(self, user_id, summary):
        if user_id not in self.submission_history:
            self.submission_history[user_id] = []
        self.submission_history[user_id].append(summary)

    @virustotal.command(name="history", aliases=["sh"])
    async def submission_history(self, ctx):
        """View files recently submitted by you"""
        user_id = ctx.author.id
        if user_id in self.submission_history and self.submission_history[user_id]:
            history = "\n".join(self.submission_history[user_id])
            embed = discord.Embed(title="Your recent VirusTotal submissions", description=history, colour=discord.Colour(0x2BBD8E))
        else:
            embed = discord.Embed(title="No recent submissions", description="You have not submitted any files for analysis yet. Submissions reset when the bot restarts.", colour=discord.Colour(0xff4545))
        await ctx.send(embed=embed)


