import requests
import re
import json
import discord
from redbot.core import commands
from redbot.core import app_commands

class Malcore(commands.Cog):
    """Malcore file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(name="urlcheck", description="Submit content to Malcore for deep analysis")
    async def urlcheck(self, ctx, url: str):
        mcore_key = await self.bot.get_shared_api_tokens("malcore")
        if mcore_key.get("api_key") is None:
            await ctx.send("The Malcore API key has not been set.")
        if url == "":
            await ctx.send("Please define a URL!")
        if "http" not in url and "https" not in url:
            await ctx.send("Please provide a valid URL!")
        headers = {
            "apiKey": mcore_key["api_key"]
        }
        data = {
            "url": url
        }
        await ctx.message.delete()
        try:
            async with ctx.typing():
                r = requests.post('https://api.malcore.io/api/urlcheck', headers=headers, data=data)
                res = r.text
                json_data = json.loads(res)
                threat_level = json_data.get("data", {}).get("data", {}).get("threat_level")
                embed = discord.Embed(url=f"{url}")
                if threat_level and "SAFE" in threat_level:
                    embed.title = f"{url} looks safe"
                    embed.color = 0x2BBD8E  # Green color
                    embed.description = f"Malcore did not detect any threats associated with this URL"
                    embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                else:
                    embed.title = f"{url} looks malicious!"
                    embed.description = f"One or more security vendors have marked this URL as potentially dangerous.\n\nFor your own safety, you should not open, launch, or interact with it."
                    embed.color = 0xFF4545  # Red color
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                await ctx.send(embed=embed)
        except json.JSONDecodeError:
            await ctx.send(f"Invalid JSON response from Malcore API.")