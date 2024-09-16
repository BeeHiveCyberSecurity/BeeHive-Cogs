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
        
    @abuseipdb.command(name="reports", description="Check reports for an IP address against AbuseIPDB.")
    async def reports(self, ctx, ip: str, page: int = 1, per_page: int = 25):
        api_key = await self.config.guild(ctx.guild).api_key()
        if not api_key:
            await ctx.send("API key not set. Use the setapikey command to set it.")
            return

        abuseipdb_url = "https://api.abuseipdb.com/api/v2/reports"
        headers = {
            "Key": api_key,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": ip,
            "page": page,
            "perPage": per_page
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(abuseipdb_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    report_data = data['data']
                    if not report_data['results']:
                        await ctx.send(f"No reports found for IP address {ip}.")
                        return

                    embeds = []
                    for i, rep in enumerate(report_data['results']):
                        embed = discord.Embed(title=f"AbuseIPDB reports for {ip} (Page {page}/{report_data['lastPage']})", color=0xfffffe)
                        embed.set_footer(text=f"Total reports: {report_data['total']}")
                        embed.add_field(
                            name=f"Report {i+1}",
                            value=f'**<t:{int(discord.utils.parse_time(rep["reportedAt"]).timestamp())}:R>**, "{rep["comment"]}"\n'
                                  f'Categories: {", ".join(map(str, rep["categories"]))}\n'
                                  f'Reporter: {rep["reporterId"]} ({rep["reporterCountryName"]})',
                            inline=False
                        )
                        embeds.append(embed)

                    message = await ctx.send(embed=embeds[0])

                    if len(embeds) > 1:
                        await message.add_reaction("⬅️")
                        await message.add_reaction("➡️")

                        def check(reaction, user):
                            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

                        current_page = 0
                        while True:
                            try:
                                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                                if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                                    current_page += 1
                                    await message.edit(embed=embeds[current_page])
                                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                                    current_page -= 1
                                    await message.edit(embed=embeds[current_page])
                                await message.remove_reaction(reaction, user)
                            except asyncio.TimeoutError:
                                break
                else:
                    await ctx.send("Failed to fetch data from AbuseIPDB.")

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
                    embed = discord.Embed(title=f"AbuseIPDB report for {ip}", color=0xfffffe)
                    embed.add_field(name="IP address", value=report['ipAddress'], inline=True)
                    embed.add_field(name="Abuse confidence score", value=report['abuseConfidenceScore'], inline=True)
                    embed.add_field(name="Country", value=f"{report['countryName']} ({report['countryCode']})", inline=True)
                    embed.add_field(name="ISP", value=report['isp'], inline=True)
                    embed.add_field(name="Domain", value=report['domain'], inline=True)
                    embed.add_field(name="Total reports", value=report['totalReports'], inline=True)
                    embed.add_field(name="Last reported", value=f"**<t:{int(discord.utils.parse_time(report['lastReportedAt']).timestamp())}:R>**", inline=True)
                    if report['reports']:
                        for i, rep in enumerate(report['reports'][:5]):
                            embed.add_field(
                                name=f"Report {i+1}",
                                value=f'**<t:{int(discord.utils.parse_time(rep["reportedAt"]).timestamp())}:R>**, "{rep["comment"]}"',
                                inline=False
                            )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Failed to fetch data from AbuseIPDB.")


