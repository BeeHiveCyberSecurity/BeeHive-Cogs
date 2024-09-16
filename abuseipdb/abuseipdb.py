import discord #type: ignore
from redbot.core import commands, Config #type: ignore
import aiohttp #type: ignore

class AbuseIPDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_guild = {
            "api_key": None
        }
        self.config.register_guild(**default_guild)

    @commands.group(name="abuseipdb")
    async def abuseipdb(self, ctx):
        """Interact with the AbuseIPDB API"""

    @abuseipdb.command(name="setapikey", description="Set the API key for AbuseIPDB.")
    @commands.has_permissions(manage_guild=True)
    async def setapikey(self, ctx, api_key: str):
        await self.config.guild(ctx.guild).api_key.set(api_key)
        await ctx.send("API key set successfully.")

    @abuseipdb.command(name="checkip", description="Check an IP address against AbuseIPDB.")
    async def checkip(self, ctx, ip: str):
        api_key = await self.config.guild(ctx.guild).api_key()
        if not api_key:
            await ctx.send("API key not set. Use the setapikey command to set it.")
            return

        abuseipdb_url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Key": api_key,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": ip
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(abuseipdb_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    await ctx.send(f"IP Address: {ip}\nAbuse Confidence Score: {data['data']['abuseConfidenceScore']}")
                else:
                    await ctx.send("Failed to fetch data from AbuseIPDB.")


