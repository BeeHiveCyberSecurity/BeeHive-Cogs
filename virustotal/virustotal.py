from redbot.core import commands

class VirusTotal(commands.Cog):
    """Virus Total Inspection"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def virustotal(self, ctx):
        vt_key = await self.bot.get_shared_api_tokens("virustotal")
        if vt_key.get("api_key") is None:
            return await ctx.send("The Virus Total API key has not been set.")
        else:
            return await ctx.send("Virus Total Key Found")