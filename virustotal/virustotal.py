import requests
import discord
from redbot.core import commands

class VirusTotal(commands.Cog):
    """Virus Total Inspection"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def virustotal(self, ctx, file_url: str = None):
        await ctx.message.delete()
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        if vt_key.get("api_key") is None:
            return await ctx.send("The Virus Total API key has not been set.")
        else:
            if file_url:
                response = requests.get(file_url)
                if response.status_code != 200:
                    embed_error = discord.Embed(title="**[** ``Error`` **]**", color=0x7F00FF)
                    embed_error.add_field(name="", value="\u200a", inline=False)
                    embed_error.add_field(name="Download Error:", value=f"Failed to download the file!", inline=False)
                    await ctx.message.delete()
                    original_message_error = await ctx.send(embed=embed_error)
                    await original_message_error.delete(delay=10)
                    return
                file_url = file_url.split("?")[0]
                response = requests.get(file_url)
                file_content = response.content
                file_name = file_url.split("/")[-1]
            else:
                attachment = ctx.message.attachments[0]
                file_content = await attachment.read()
                file_name = attachment.filename
                vt_params = {"apikey": vt_key["api_key"]}
                files = {"file": (file_name, file_content)}
                response = requests.post("https://www.virustotal.com/vtapi/v2/file/scan", files=files, params=vt_params)
                json_response = response.json()
                embed_response = discord.Embed(title="**[** ``VirusTotal`` **]**", color=0x00FF00)
                embed_response.add_field(name="", value="\u200a", inline=False)
                embed_response.add_field(name="Scan Result:", value=json_response["verbose_msg"], inline=False)
                embed_response.add_field(name="Permalink:", value=json_response["permalink"], inline=False)
                await ctx.send(embed=embed_response)