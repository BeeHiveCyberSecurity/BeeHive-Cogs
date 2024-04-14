import requests
import re, json
import discord
from redbot.core import commands

class Malcore(commands.Cog):
    """malcore file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.process_urls())

    async def checkurl(self, file_url, ctx):
        mcore_key = await self.bot.get_shared_api_tokens("malcore")
        if mcore_key.get("api_key") is None:
            return await ctx.send("The Malcore API key has not been set.")
        if file_url == "":
            await ctx.send("Please Define A URL!")
        if "http" not in file_url and "https" not in file_url:
            await ctx.send("Please Provide A Valid URL!")
        if file_url:
            headers = {
                "apiKey": mcore_key["api_key"]
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
                    await ctx.send(f"The URL is SAFE.\nDEBUG: ```{json_data}```")
                else:
                    await ctx.send("The URL might be unsafe.")
            except json.JSONDecodeError:
                await ctx.send(f"Invalid JSON response from Malcore API.\nDEBUG: ```{res}```")
        else:
            await ctx.send("No URL provided.")


    @commands.command()
    async def malcore(self, ctx, url: str):
        async with ctx.typing():
            await ctx.message.delete()
            await self.checkurl(url, ctx)
                    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        url_pattern = re.compile(
            r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+")

        urls = url_pattern.findall(message.content)
        for url in urls:
            await self.url_queue.put(url)
            
    async def process_urls(self):
            while True:
                url = await self.url_queue.get()
                await self.checkurl(url, ctx=None)