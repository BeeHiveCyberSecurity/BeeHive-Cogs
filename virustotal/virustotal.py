import aiohttp #type: ignore
import io
import os
import tempfile
import math
import asyncio
import discord #type: ignore
import matplotlib.pyplot as plt #type: ignore
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
                                await self.check_results(ctx, permalink, ctx.author.id)
                            else:
                                raise ValueError("No permalink found in the response.")
                    elif attachments:
                        attachment = attachments[0]
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
                                    # Delete the attachment message from the channel
                                    await ctx.message.delete()
                                else:
                                    raise ValueError("No analysis ID found in the response.")
                    else:
                        embed = discord.Embed(title='Error: No file provided', description="The bot was unable to find content to submit for analysis!\nPlease provide one of the following when using this command:\n- URL file can be downloaded from\n- Drag-and-drop a file less than 25mb in size\n- Reply to a message containing a file", colour=discord.Colour(0xff4545))
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                        await ctx.send(embed=embed)
                except (aiohttp.ClientResponseError, ValueError) as e:
                    embed = discord.Embed(title='Error: Failed to submit file', description=str(e), colour=discord.Colour(0xff4545))
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                    await ctx.send(embed=embed)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title='Error: Request Timeout', description="The bot was unable to complete the request due to a timeout.", colour=discord.Colour(0xff4545))
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close.png")
                    await ctx.send(embed=embed)

    async def check_results(self, ctx, analysis_id, presid):
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
                        labels = ['Malicious', 'Suspicious', 'No Verdict', 'Harmless', 'Failed', 'Unsupported']
                        sizes = [malicious_count, suspicious_count, undetected_count, harmless_count, failure_count, unsupported_count]
                        colors = ['#ff4545', '#ff9144', '#dddddd', '#2BBD8E', '#ffcccb', '#ececec']

                        # Create a bar chart instead of a spider graph
                        plt.figure(figsize=(8, 6))
                        ax = plt.subplot(111)

                        # Create the bar chart
                        ax.bar(labels, sizes, color=colors)

                        # Add some text for labels, title and custom x-axis tick labels, etc.
                        ax.set_ylabel('Verdicts')
                        ax.set_title('Vendor ratings summary')
                        ax.set_xticks(labels)
                        ax.set_xticklabels(labels)
                        ax.legend()

                        # Attach a text label above each bar in *rects*, displaying its height.
                        for rect in ax.patches:
                            height = rect.get_height()
                            ax.annotate('{}'.format(height),
                                        xy=(rect.get_x() + rect.get_width() / 2, height),
                                        xytext=(0, 3),  # 3 points vertical offset
                                        textcoords="offset points",
                                        ha='center', va='bottom')

                        # Save the bar chart as a PNG image in memory.
                        bar_chart_buffer = io.BytesIO()
                        plt.savefig(bar_chart_buffer, format='png')
                        bar_chart_buffer.seek(0)  # rewind the buffer to the beginning so we can read its content

                        # Set the bar chart image as the embed image
                        embed.set_image(url="attachment://bar_chart.png")

                        # Clear the matplotlib figure
                        plt.clf()
                        plt.close('all')

                        # Create a discord file from the image in memory
                        bar_chart_file = discord.File(bar_chart_buffer, filename='bar_chart.png')
                        if malicious_count >= 11:
                            embed.title = "Malicious file found"
                            embed.description = f"# {int(percent)}% of security vendors rated this file dangerous!\nYou should avoid this file completely, and delete it from your systems to ensure security."
                            embed.color = discord.Colour(0xff4545)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                        elif 1 < malicious_count < 11:
                            embed.title = "Suspicious file found"
                            embed.description = f"# {int(percent)}% of security vendors rated this file dangerous!\nWhile there are malicious ratings available for this file, there aren't many, so this could be a false positive. **You should investigate further.**"
                            embed.color = discord.Colour(0xff9144)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Orange/alert-circle-outline.png")
                        else:
                            embed.title = "No threat found"
                            embed.color = discord.Colour(0x2BBD8E)
                            embed.description = "# No security vendors currently flag this file as malicious\nYou should be safe to run and use it. Check back on the results later to see if vendors change their minds - it happens"
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")

                        embed.add_field(name="MD5", value=f"**`{md5}`**", inline=False)
                        embed.add_field(name="SHA-1", value=f"**`{sha1}`**", inline=False)
                        embed.add_field(name="SHA-256", value=f"**`{sha256}`**", inline=False)

                        # Create the button for the virustotal results link
                        button = discord.ui.Button(label="View results on VirusTotal", url=f"https://www.virustotal.com/gui/file/{sha256}", emoji="🌐", style=discord.ButtonStyle.url)
                        button2 = discord.ui.Button(label="Get a second opinion", url="https://discord.gg/6PbaH6AfvF", style=discord.ButtonStyle.url)
                        view = discord.ui.View()
                        view.add_item(button)
                        view.add_item(button2)
                        await ctx.send(content=content, file=bar_chart_file, embed=embed, view=view)
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


