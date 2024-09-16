import discord #type: ignore
from redbot.core import commands, Config #type: ignore
import aiohttp #type: ignore
import asyncio
import ipaddress

class AbuseIPDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_guild = {
            "api_key": None
        }
        self.config.register_guild(**default_guild)

    @commands.group(name="abuseipdbset")
    async def abuseipdbset(self, ctx):
        """Configure the AbuseIPDB cog"""

    @abuseipdbset.command(name="setapikey", description="Set the API key for AbuseIPDB.")
    @commands.admin_or_permissions()
    async def setapikey(self, ctx, api_key: str):
        await self.config.guild(ctx.guild).api_key.set(api_key)
        await ctx.send("API key set successfully.")
    
    @commands.group(name="abuseipdb")
    async def abuseipdb(self, ctx):
        """
        AbuseIPDB is a project to help combat the spread of hackers, spammers, and abusive activity on the internet by providing a central blacklist for webmasters, system administrators, and other interested parties to report IP's engaged in bad behavior.

        Learn more at https://www.abuseipdb.com
        """
    
    @abuseipdb.command(name="report", description="Report an IP address to AbuseIPDB.")
    async def report(self, ctx):
        """Create a new IP abuse report"""
        api_key = await self.config.guild(ctx.guild).api_key()
        if not api_key:
            await ctx.send("API key not set. Use the setapikey command to set it.")
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        async def get_user_input(prompt):
            embed = discord.Embed(
                title="Information needed...",
                description=prompt,
                color=0xfffffe
            )
            message = await ctx.send(embed=embed)
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                if msg.content.lower() == "cancel":
                    cancel_embed = discord.Embed(
                        title="Report cancelled",
                        description="You have cancelled your report. Start a new report at any time using `[p]abuseipdb report`.",
                        color=0xff4545
                    )
                    await ctx.send(embed=cancel_embed)
                    await message.delete()
                    await msg.delete()
                    return None
                await message.delete()
                await msg.delete()
                return msg.content
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout",
                    description="You took too long to respond. Please try the command again.",
                    color=0xff4545
                )
                await ctx.send(embed=timeout_embed)
                await message.delete()
                return None

        embed = discord.Embed(
            title="Before you get started, here's what you need to know",
            description=(
                "To report an IP address, you will need to provide the following information:\n"
                "**1.** The **IP address** you want to report.\n"
                "**2.** The **categories of abuse** (comma-separated).\n"
                "**3.** A **comment describing** the abuse.\n\n"
                "### Tips and suggestions\n"
                "- Make sure the IP address is correct.\n"
                "- Provide detailed and accurate context as your comment.\n"
                "- You can cancel the report at any time by typing `cancel`.\n"
            ),
            color=0xfffffe
        )
        message = await ctx.send(embed=embed)

        ip = await get_user_input("Please respond in chat with the IPv4 or IPv6 that you'd like to create a report for.")
        if ip is None:
            await message.delete()
            return

        categories_table = (
            "**1** DNS Compromise\n"
            "**2** DNS Poisoning\n"
            "**3** Fraud Orders\n"
            "**4** DDoS Attack\n"
            "**5** FTP Brute-Force\n"
            "**6** Ping of Death\n"
            "**7** Phishing\n"
            "**8** Fraud VoIP\n"
            "**9** Open Proxy\n"
            "**10** Web Spam\n"
            "**11** Email Spam\n"
            "**12** Blog Spam\n"
            "**13** VPN IP\n"
            "**14** Port Scan\n"
            "**15** Hacking\n"
            "**16** SQL Injection\n"
            "**17** Spoofing\n"
            "**18** Brute-Force\n"
            "**19** Bad Web Bot\n"
            "**20** Exploited Host\n"
            "**21** Web App Attack\n"
            "**22** SSH\n"
            "**23** IoT Targeted"
        )
        categories = await get_user_input(f"Please enter the categories (comma-separated) for the report\n\n{categories_table}")
        if categories is None:
            await message.delete()
            return

        comment = await get_user_input("Please enter a comment for the report")
        if comment is None:
            await message.delete()
            return

        await message.delete()

        abuseipdb_url = "https://api.abuseipdb.com/api/v2/report"
        headers = {
            "Key": api_key,
            "Accept": "application/json"
        }
        data = {
            "ip": ip,
            "categories": categories,
            "comment": comment,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with ctx.typing():
                try:
                    async with session.post(abuseipdb_url, data=data) as response:
                        response_data = await response.json()
                        if response.status == 200:
                            ip_address = response_data["data"]["ipAddress"]
                            abuse_confidence_score = response_data["data"]["abuseConfidenceScore"]
                            embed = discord.Embed(
                                title="Your report was successfully processed",
                                description="Reports like yours help assist security analysts and sysadmins around the world who rely on AbuseIPDB",
                                color=0x2bbd8e
                            )
                            embed.add_field(name="IP address reported", value=ip_address, inline=True)
                            embed.add_field(name="Updated abuse score", value=abuse_confidence_score, inline=True)
                            await ctx.send(embed=embed)
                        else:
                            error_detail = response_data["errors"][0]["detail"]
                            embed = discord.Embed(
                                title="Something went wrong",
                                description=error_detail,
                                color=0xff4545
                            )
                            await ctx.send(embed=embed)
                except aiohttp.ClientError as e:
                    embed = discord.Embed(
                        title="Client Error",
                        description=f"An error occurred while trying to report the IP address: {str(e)}",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                except Exception as e:
                    embed = discord.Embed(
                        title="Unexpected Error",
                        description=f"An unexpected error occurred: {str(e)}",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)

    @abuseipdb.command(name="list", description="Check reports for an IP address against AbuseIPDB.")
    async def list(self, ctx, ip: str):
        """Show all reports for an IP"""
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
            "page": 1,
            "perPage": 100
        }

        reason_map = {
            1: "DNS Compromise",
            2: "DNS Poisoning",
            3: "Fraud Orders",
            4: "DDoS Attack",
            5: "FTP Brute-Force",
            6: "Ping of Death",
            7: "Phishing",
            8: "Fraud VoIP",
            9: "Open Proxy",
            10: "Web Spam",
            11: "Email Spam",
            12: "Blog Spam",
            13: "VPN IP",
            14: "Port Scan",
            15: "Hacking",
            16: "SQL Injection",
            17: "Spoofing",
            18: "Brute-Force",
            19: "Bad Web Bot",
            20: "Exploited Host",
            21: "Web App Attack",
            22: "SSH",
            23: "IoT Targeted"
        }

        all_reports = []
        async with aiohttp.ClientSession(headers=headers) as session:
            async with ctx.typing():
                async with session.get(abuseipdb_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        report_data = data['data']
                        total_reports = report_data['total']
                        pages = (total_reports // params["perPage"]) + (1 if total_reports % params["perPage"] != 0 else 0)
                        
                        for page in range(1, pages + 1):
                            params["page"] = page
                            async with session.get(abuseipdb_url, params=params) as page_response:
                                if page_response.status == 200:
                                    page_data = await page_response.json()
                                    all_reports.extend(page_data['data']['results'])
                                else:
                                    await ctx.send("Failed to fetch data from AbuseIPDB.")
                                    return
                    else:
                        await ctx.send("Failed to fetch data from AbuseIPDB.")
                        return

        if not all_reports:
            await ctx.send(f"No reports found for IP address {ip}.")
            return

        embeds = []
        for i, rep in enumerate(all_reports):
            categories = [reason_map.get(cat, f"Unknown ({cat})") for cat in rep["categories"]]
            embed = discord.Embed(title=f"AbuseIPDB reports for {ip}", color=0xfffffe)
            embed.set_footer(text=f"Total reports: {len(all_reports)}")
            embed.add_field(
                name=f"Report {i+1}",
                value=f'**<t:{int(discord.utils.parse_time(rep["reportedAt"]).timestamp())}:R>** for {", ".join(categories)}\n'
                      f'Report says "{rep["comment"]}"\n'
                      f'Reported by user `{rep["reporterId"]}` in **{rep["reporterCountryName"]}**',
                inline=False
            )
            embeds.append(embed)

        message = await ctx.send(embed=embeds[0])

        if len(embeds) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("❌")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

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
                    elif str(reaction.emoji) == "❌":
                        break
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break
            await message.clear_reactions()

    @abuseipdb.command(name="check", description="Check an IP address against AbuseIPDB.")
    async def checkip(self, ctx, ip: str):
        """See details about an IPv4 or IPv6"""

        # Validate IP address
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            await ctx.send("Invalid IP address. Please provide a valid IPv4 or IPv6 address.")
            return

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


