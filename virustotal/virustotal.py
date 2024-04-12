import requests
import asyncio
import discord
from redbot.core import commands
import time, json
import io

class VirusTotal(commands.Cog):
    """Virus Total Inspection"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if vt_key.get("api_key") is None:
                return await ctx.send("The Virus Total API key has not been set.")
            else:
                if file_url:
                    response = requests.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": vt_key["api_key"]}, data={"url": file_url})
                    data = response.json()
                    if "permalink" in data:
                        permalink = data["permalink"]
                        await ctx.send(f"Permalink: {permalink.split('-')[1]}")
                        await self.check_results(ctx, permalink.split('-')[1])
                        await ctx.message.delete()
                    else:
                        await ctx.send("Failed to submit the file for analysis.")
                elif ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    response = requests.get(attachment.url)
                    if response.status_code != 200:
                        return await ctx.send("Failed to download the attached file.")
                    file_content = response.content
                    response = requests.post("https://www.virustotal.com/api/v3/files", headers={"x-apikey": vt_key["api_key"]}, files={"file": file_content})
                    data = response.json()
                    analysis = data['data']['id']
                    await self.check_results(ctx, analysis)
                    await ctx.message.delete()
                else:
                    await ctx.send("No file URL or attachment provided.")

    async def check_results(self, ctx, analysis_id):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        headers = {"x-apikey": vt_key["api_key"]}
        while True:
            response = requests.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', headers=headers)
            data = response.json()
            if "data" in data:
                attributes = data["data"].get("attributes")
                if attributes and attributes.get("status") == "completed":
                    stats = attributes.get("stats", {})
                    malicious_count = stats.get("malicious", 0)
                    suspicious_count = stats.get("suspicious", 0)
                    undetected_count = stats.get("undetected", 0)
                    harmless_count = stats.get("harmless", 0)
                    timeout_count = stats.get("timeout", 0)
                    confirmed_timeout_count = stats.get("confirmed-timeout", 0)
                    failure_count = stats.get("failure", 0)
                    unsupported_count = stats.get("type-unsupported", 0)
                    meta = data.get("meta", {}).get("file_info", {})
                    fulllink = meta.get("sha256")
                    if malicious_count > 0:
                        embed = discord.Embed(title="File Analysis Completed", url=f"https://www.virustotal.com/gui/file/{fulllink}", color=15158332)
                    else:
                        embed = discord.Embed(title="File Analysis Completed", url=f"https://www.virustotal.com/gui/file/{fulllink}", color=0x00ff00)
                    embed.add_field(name="Status", value="Completed", inline=False)
                    embed.add_field(name="Malicious Count", value=malicious_count, inline=False)
                    if malicious_count > 0:
                        malicious_engines = []
                        for engine, result in attributes["results"].items():
                            if result.get("category") == "malicious":
                                malicious_engines.append(engine)
                        embed.add_field(name="Malicious Engines", value=", ".join(malicious_engines), inline=False)
                    embed.add_field(name="Suspicious Count", value=suspicious_count, inline=False)
                    embed.add_field(name="Undetected Count", value=undetected_count, inline=False)
                    embed.add_field(name="Harmless Count", value=harmless_count, inline=False)
                    embed.add_field(name="Timeout Count", value=timeout_count, inline=False)
                    embed.add_field(name="Confirmed Timeout Count", value=confirmed_timeout_count, inline=False)
                    embed.add_field(name="Failure Count", value=failure_count, inline=False)
                    embed.add_field(name="Unsupported Count", value=unsupported_count, inline=False)
                    await ctx.send(embed=embed)
                    break
            await asyncio.sleep(3)