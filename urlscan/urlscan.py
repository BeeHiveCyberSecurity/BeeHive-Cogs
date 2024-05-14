import requests
import discord #type: ignore
import json
import time
import re
from redbot.core import commands #type: ignore 
from redbot.core import app_commands #type: ignore

class URLScan(commands.Cog):
    """URLScan file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(name="urlscan", description="Utilize URLScan's /scan endpoint to scan a URL")
    async def urlscan(self, ctx, *, urls: str = None):
        urlscan_key = await self.bot.get_shared_api_tokens("urlscan")
        if urlscan_key.get("api_key") is None:
            await ctx.send("The URLScan API key has not been set.")
            return

        if urls is None:
            if ctx.message.reference and ctx.message.reference.resolved:
                ref_msg = ctx.message.reference.resolved
                urls = ref_msg.content
            else:
                await ctx.send("Please provide a URL or reply to a message with URLs!")
                return

        urls_to_scan = re.findall(r'(https?://\S+)', urls)
        if not urls_to_scan:
            await ctx.send("No valid URLs found to scan.")
            return

        headers = {
            "Content-Type": "application/json",
            "API-Key": urlscan_key["api_key"]
        }

        for url in urls_to_scan:
            data = {"url": url, "visibility": "public"}
            try:
                async with ctx.typing():
                    r = requests.post('https://urlscan.io/api/v1/scan/', headers=headers, data=json.dumps(data), timeout=10)
                    res = r.json()
                    if 'result' not in res:
                        await ctx.send(f"{res.get('message', 'Unknown error')}")
                        continue

                    report_url = res['result']
                    report_api = res['api']
                    time.sleep(10)
                    r2 = requests.get(report_api, timeout=60)
                    res2 = r2.json()

                    embed = discord.Embed(url=report_url)
                    if 'verdicts' in res2 and 'overall' in res2['verdicts'] and 'score' in res2['verdicts']['overall']:
                        threat_level = res2['verdicts']['overall']['score']
                        if threat_level != 0:
                            embed.title = f"This URL looks suspicious!"
                            embed.description = f"URLScan says {url} is suspicious!\n\nFor your own safety, please don't click it."
                            embed.color = 0xFF4545
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                        else:
                            embed.title = f"That URL looks safe"
                            embed.color = 0x2BBD8E
                            embed.description = f"URLScan did not detect any threats associated with {url}"
                            embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                    else:
                        embed.title = f"Error occurred during URLScan"
                        embed.description = f"Unable to determine the threat level for {url}."
                        embed.color = 0xFFD700
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/warning-outline.png")

                    await ctx.send(embed=embed)
            except (json.JSONDecodeError, requests.exceptions.Timeout):
                await ctx.send(f"Invalid JSON response from URLScan API or request timed out for {url}.")
