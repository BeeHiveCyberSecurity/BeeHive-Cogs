import requests
import re
import json
import discord
from redbot.core import commands

class Malcore(commands.Cog):
    """malcore file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def malcore(self, ctx, url: str):
        mcore_key = await self.bot.get_shared_api_tokens("malcore")
        if mcore_key.get("api_key") is None:
            return await ctx.send("The Malcore API key has not been set.")
        if url == "":
            return await ctx.send("Please define a URL!")
        if "http" not in url and "https" not in url:
            return await ctx.send("Please provide a valid URL!")
        headers = {
            "apiKey": mcore_key["api_key"]
        }
        data = {
            "url": url
        }
        try:
            async with ctx.typing():
                r = requests.post('https://api.malcore.io/api/urlcheck', headers=headers, data=data)
                res = r.text
                json_data = json.loads(res)
                threat_level = json_data.get("data", {}).get("data", {}).get("threat_level")
                embed = discord.Embed(url=f"{url}")
                if threat_level and "SAFE" in threat_level:
                    embed.title = f"That file looks safe!"
                    embed.color = 0x2BBD8E  # Green color
                    embed.description = f"There's nothing obviously malicious about this URL - it should be safe."
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
        await ctx.message.delete()
