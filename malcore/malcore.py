import requests
import re, json
import discord
from redbot.core import commands

class Malcore(commands.Cog):
    """malcore file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def malcore(self, ctx, file_url: str):
        async with ctx.typing():
            await ctx.message.delete()
            mcore_key = await self.bot.get_shared_api_tokens("malcore")
            if mcore_key.get("api_key") is None:
                return await ctx.send("The Malcore API key has not been set.")
            if file_url == "":
                await ctx.send("Please Define A URL!")
            if file_url:
                
                headers = {
                    "apiKey" : mcore_key["api_key"]
                }
                
                data = {
                    "url": file_url
                }
                
                r = requests.post('https://api.malcore.io/api/urlcheck', headers=headers, data=data)
                res = r.text
                
                try:
                    json_data = json.loads(res)
                    threat_level = json_data.get("data", {}).get("data", {}).get("threat_level")
                    if threat_level and "SAFE" in threat_level:
                        await ctx.send("The URL is SAFE.")
                    else:
                        await ctx.send("The URL might be unsafe.")
                except json.JSONDecodeError:
                    await ctx.send("Invalid JSON response from Malcore API.")
            else:
                await ctx.send("No URL provided.")
            
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        url_pattern = re.compile(r"^(?:http[s]?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")

        if url_pattern.search(message.content):
            await message.delete()
            await message.author.send("Ay Fuck You Were Testing Here!")
                
    # async def check_results(self, ctx, analysis_id, presid):
    #     vt_key = await self.bot.get_shared_api_tokens("virustotal")
    #     headers = {"x-apikey": vt_key["api_key"]}
        
    #     while True:
    #         response = requests.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers)
    #         data = response.json()
            
    #         if "data" in data:
    #             attributes = data["data"].get("attributes")
    #             if attributes and attributes.get("status") == "completed":
    #                 stats = attributes.get("stats", {})
    #                 malicious_count = stats.get("malicious", 0)
    #                 suspicious_count = stats.get("suspicious", 0)
    #                 undetected_count = stats.get("undetected", 0)
    #                 harmless_count = stats.get("harmless", 0)
    #                 failure_count = stats.get("failure", 0)
    #                 unsupported_count = stats.get("type-unsupported", 0)
    #                 meta = data.get("meta", {}).get("file_info", {}).get("sha256")
                    
    #                 if meta:
    #                     embed = discord.Embed(url=f"https://www.virustotal.com/gui/file/{meta}")
    #                     if malicious_count > 0:
    #                         content = f"||<@{presid}>||"
    #                         embed.title = f"That file looks malicious!"
    #                         embed.description = f"One or more security vendors have marked this file as potentially dangerous.\n\nFor your own safety, you should not open, launch, or interact with it."
    #                         embed.color = 0xFF4545  # Red color
    #                         embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
    #                     else:
    #                         content = f"||<@{presid}>||"
    #                         embed.title = f"That file looks safe!"
    #                         embed.color = 0x2BBD8E  # Green color
    #                         embed.description = f"There's nothing obviously malicious about this file - it should be safe."
    #                         embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
    #                         embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                        
    #                     total_count = malicious_count + suspicious_count + undetected_count + harmless_count + failure_count + unsupported_count
    #                     percentpre = malicious_count / total_count if total_count > 0 else 0
    #                     percent = round(percentpre * 100, 2)
    #                     embed.add_field(name="Analysis results", value=f"**{percent}% of security vendors rated this file dangerous!**\n({malicious_count} malicious, {undetected_count} clean)", inline=False)

    #                     await ctx.send(content, embed=embed)
    #                     break
    #                 else:
    #                     await ctx.send("Error: SHA256 value not found in the analysis response.")
    #                     break
    #         else:
    #             await ctx.send("Error: Analysis ID not found or analysis not completed yet.")
    #             break
            
    #         try:
    #             await ctx.message.delete()
    #         except discord.errors.NotFound:
    #             pass
            
    #         await asyncio.sleep(3)