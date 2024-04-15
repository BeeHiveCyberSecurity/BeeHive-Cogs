import requests, discord, json
from redbot.core import commands
from redbot.core import app_commands

class URLScan(commands.Cog):
    """URLScan file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(name="urlscan", description="Utilize URLScan's /scan endpoint to scan a URL")
    async def urlscan(self, ctx, url: str):
        urlscan_key = await self.bot.get_shared_api_tokens("urlscan")
        if urlscan_key.get("api_key") is None:
            await ctx.send("The URLScan API key has not been set.")
        if url == "":
            await ctx.send("Please define a URL!")
        if "http" not in url and "https" not in url:
            await ctx.send("Please provide a valid URL!")
        headers = {
            "Content-Type: application/json"
            "API-Key": urlscan_key["api_key"]
        }
        data = {"url": f"{url}", "visibility": "public"}
        try:
            async with ctx.typing():
                r = requests.post('https://urlscan.io/api/v1/scan/', headers=headers, data=json.dumps(data))
                res = r.json
                report_url = res['result']
                r2 = requests.get(f"{res['api']}")
                res2 = r2.json()
                embed = discord.Embed(url=f"{report_url}")
                threat_level = res2['verdicts']['overall']['score']
                if threat_level and "0" in threat_level:
                    embed.title = f"That URL looks safe"
                    embed.color = 0x2BBD8E  # Green color
                    embed.description = f"URLScan did not detect any threats associated with {url}"
                    embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                else:
                    embed.title = f"This URL looks suspicious!"
                    embed.description = f"URLScan says {url} is suspicious!\n\nFor your own safety, please don't click it."
                    embed.color = 0xFF4545  # Red color
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                await ctx.send(embed=embed)
        except json.JSONDecodeError:
            await ctx.send(f"Invalid JSON response from URLScan API.")