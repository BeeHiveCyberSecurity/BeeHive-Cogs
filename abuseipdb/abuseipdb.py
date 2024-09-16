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
    @commands.admin_or_permissions()
    async def setapikey(self, ctx, api_key: str):
        await self.config.guild(ctx.guild).api_key.set(api_key)
        await ctx.send("API key set successfully.")

    @abuseipdb.command(name="check", description="Check an IP address against AbuseIPDB.")
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
            "ipAddress": ip,
            "verbose": ""
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(abuseipdb_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    report = data['data']
                    embed = discord.Embed(title=f"AbuseIPDB Report for {ip}", color=0xfffffe
                    embed.add_field(name="IP Address", value=report['ipAddress'], inline=True)
                    embed.add_field(name="Abuse Confidence Score", value=report['abuseConfidenceScore'], inline=True)
                    embed.add_field(name="Country", value=f"{report['countryName']} ({report['countryCode']})", inline=True)
                    embed.add_field(name="ISP", value=report['isp'], inline=True)
                    embed.add_field(name="Domain", value=report['domain'], inline=True)
                    embed.add_field(name="Total Reports", value=report['totalReports'], inline=True)
                    embed.add_field(name="Last Reported At", value=report['lastReportedAt'], inline=True)
                    if report['reports']:
                        latest_report = report['reports'][0]
                        embed.add_field(name="Latest Report", value=f"Reported At: {latest_report['reportedAt']}\nComment: {latest_report['comment']}", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Failed to fetch data from AbuseIPDB.")


