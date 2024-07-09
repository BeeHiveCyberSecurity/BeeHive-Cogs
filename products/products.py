import asyncio
import aiohttp
import time
import json
import io
import discord # type: ignore
from redbot.core import commands # type: ignore


class Products(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antivirus_links = {
            1147002526156206170: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",  # BeeHive
            1229268715208577034: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",  # Holy Hangout
            1173631740305215558: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",  # Storm AntiCheat
            1216201978024169482: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",  # Storm Development
            1130836986962395259: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",   # Paradigm Intel
            1235457477072654386: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk"   # PC Cleaning Services (Jarro's)
            # Add more server IDs and their links as needed
        }


    @commands.bot_has_permissions(embed_links=True)
    @commands.group(name="antivirus", description="Learn more about BeeHive's AntiVirus", aliases=["av"], invoke_without_command=True)
    async def antivirus(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's AntiViral/AntiMalware software

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/antivirus>)
        """
        server_id = ctx.guild.id
        server_name = ctx.guild.name
        discount_link = self.antivirus_links.get(server_id)

        embed = discord.Embed(title=f"AntiVirus / AntiMalware Security Kit", description=f"# Protect your PC from malware and spyware in just a few clicks\n\nBeeHive's security client is a security software application designed to protect users from malware or viruses while working, shopping, or playing games on their computers. It works by isolating unknown files in a safe virtual environment before performing real-time analysis to determine whether they pose any threat - all done without risk or alert fatigue for normal computer usage.", colour=16767334, url='https://www.beehive.systems/antivirus')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://i.imgur.com/NvGx5WK.png")
        embed.add_field(name="Real-Time AntiMalware", value="High-sensitivity file inspection occurs on-device to detect and block known and unknown malicious software", inline=False)
        embed.add_field(name="Real-Time AntiSpyware", value="Powerful protection from credential stealers, banking trojans, and other hard-to-detect infections", inline=False)
        embed.add_field(name="Intrusion Detection and Prevention", value="Analysis and blocking of potentially dangerous activities on the host device to preserve system integrity", inline=False)
        embed.add_field(name="Real-Time Cloud Analysis", value="Ongoing static and dynamic analysis of unknown objects within your filesystem for unidentified malware", inline=False)
        embed.add_field(name="Automated Threat Containment", value="Kernel-level API virtualization to monitor and contain unknowns during analysis and verdicting", inline=False)
        embed.add_field(name="Automated Remediation", value="No-touch, no-interaction, 100% hands free threat remediation across 7 layers of powerful protection", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Start a 15 day free trial", url="https://buy.stripe.com/5kA8y62kIg06dLqdRc", style=discord.ButtonStyle.link, emoji="<:shield:1194906995036262420>"))
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/antivirus", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)
        if discount_link:
            await ctx.typing()
            view2 = discord.ui.View()
            view2.add_item(discord.ui.Button(label="Save 30% on your first 3 months of protection", url=f"{discount_link}", style=discord.ButtonStyle.link, emoji="<:shield:1194906995036262420>"))
            embed2 = discord.Embed(title=f"Partner Perk Available", description=f"**{server_name}** is a Discord partner of BeeHive, which automatically grants this community exclusive discounts and credits", colour=16767334, url='')
            embed2.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/bag-add.png")
            embed2.add_field(name="Offer Details", value=f"Trial our Security Client for **15 days free**, then pay **only** **`$7.00`** per month until coupon expires.\n\n`Offer valid for first-time customers only, billing continues automatically unless cancelled.`", inline=False)
            await ctx.send(embed=embed2, view=view2)

    @commands.bot_has_permissions(embed_links=True)
    @antivirus.command(name="stats", description="Show weekly protection statistics")
    async def antivirusstats(self, ctx: commands.Context):
        """
        Fetch and display weekly protection statistics.
        """
        url = "https://www.xcitium.com/labs-statistics/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch statistics from Threat Lab.")
                    return
                
                page_content = await response.text()
                
                # Parse the page content to extract the statistics table
                soup = BeautifulSoup(page_content, 'html.parser')
                table = soup.find('table')
                
                if not table:
                    await ctx.send("Failed to find the statistics table.")
                    return
                
                rows = table.find_all('tr')
                if not rows:
                    await ctx.send("No data found in the statistics table.")
                    return
                
                embed = discord.Embed(title="Weekly protection statistics", description="Review weekly proof of BeeHive's proactive, detection-less protection on all endpoints.", color=0x2BBD8E, url=url)
                
                for row in rows[1:6]:  # Limit to the first 5 rows for brevity
                    columns = row.find_all('td')
                    if len(columns) >= 8:
                        week = columns[0].text.strip()
                        active_devices_potential_malicious = columns[1].text.strip()
                        active_devices_known_good = columns[2].text.strip()
                        active_devices_malicious_activity = columns[3].text.strip()
                        infection_breach = columns[4].text.strip()
                        unknowns_clean = columns[5].text.strip()
                        unknowns_pua = columns[6].text.strip()
                        unknowns_malware = columns[7].text.strip()
                        
                        embed.add_field(name=f"Week: {week}", value=(
                            f"**% of active devices with potential malicious activity:** {active_devices_potential_malicious}\n"
                            f"**% of active devices on known good state:** {active_devices_known_good}\n"
                            f"**% of active devices that had malicious activity:** {active_devices_malicious_activity}\n"
                            f"**% of Infection/Breach:** {infection_breach}\n"
                            f"**% of the unknown that turn out to be Clean:** {unknowns_clean}\n"
                            f"**% of the unknown that turn out to be PUA:** {unknowns_pua}\n"
                            f"**% of the unknown that turn out to be Malware:** {unknowns_malware}"
                        ), inline=False)
                
                await ctx.send(embed=embed)
    
    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="vulnerabilityscanning", description="Learn more about Vulnerability Scanning")
    async def vulnerabilityscanning(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's Vulnerability Scanning and Monitoring services

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/vulnerability-scanning>)
        """
        embed = discord.Embed(title=f"Vulnerability Scanning", description=f"# Scan and monitor for website and web application vulnerabilities\n\nHosting a website or web-app can cost a part-time job's worth of time to properly secure. Our Vulnerability Scanning and Vulnerability Monitoring makes it easier to know whether your changes and security mitigations are effective and help guide you on how to assume a better security posture over time.", colour=16767334, url='https://www.beehive.systems/vulnerability-scanning')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/search.png")
        embed.set_image(url="https://asset.brandfetch.io/idGpYEfxfH/id0xj4J1xg.png")
        embed.add_field(name="Know what's public", value="Discover and explore the full scope of visibility and vulnerabilities in your network, domain, or project with our detailed and carefully documented analysis. Our expert insights offer a comprehensive understanding of your system, enabling you to proactively address any potential weaknesses and bolster your defenses.", inline=True)
        embed.add_field(name="Find what's not supposed to be", value="Explore your platform's vulnerabilities, uncover hidden misconfigurations, identify vulnerable ports, and detect unpatched exploits. Our analysis equips you with the knowledge to fortify your platform's security and protect against potential threats.", inline=True)
        embed.add_field(name="Fix what's dangerous", value="Discover detailed, step-by-step instructions for effectively patching vulnerabilities and safeguarding your valuable information. Our comprehensive guides not only address weaknesses but also mitigate risks and bolster network security.", inline=False)
        embed.add_field(name="Verify it stays that way", value="Keep track of how changes in your code and dependencies affect your system. Easily compare different setups across various domains or endpoints.", inline=True)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Purchase a scan today", url="https://buy.stripe.com/14k8y64sQ15c4aQ4gg", style=discord.ButtonStyle.green, emoji="<:shield:1194906995036262420>"))
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/vulnerability-scanning", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="brandprotection", description="Learn more about Brand Protection")
    async def brandprotection(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's Brand Protection services

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/brand-protection>)
        """
        embed = discord.Embed(title=f"Brand Protection", description=f"# Stop brand abuse before it starts\n\nWe offer automated and manual scanning, reviews, takedowns, and case management to keep your brand's identity on autopilot and stop brand abuse in it's tracks", colour=16767334, url='https://www.beehive.systems/brand-protection')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://asset.brandfetch.io/idGpYEfxfH/id0xj4J1xg.png")
        embed.add_field(name="24x7 automated monitoring", value="Searches across social media and the open internet for indications of brand abuse", inline=False)
        embed.add_field(name="Expert-reviewed takedowns", value="Impede offenders by restricting and disabling services to increase cost-to-harm with human-actioned takedowns", inline=False)
        embed.add_field(name="Enhanced with artificial intelligence", value="Computer vision alongside machine learning models hunt for and validate abuse at human-plus efficiency", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/brand-protection", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="incidentresponse", description="Learn more about Incident Response", aliases=["ir"])
    async def incidentresponse(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's Incident Response services

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/incident-response>)
        """
        embed = discord.Embed(title=f"Incident Response", description=f"# Respond to potential cybersecurity incidents effectively\n\nDetect and stop breaches, empower investigation, deploy defenses, and protect business continuity", colour=16767334, url='https://www.beehive.systems/incident-response')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://asset.brandfetch.io/idGpYEfxfH/id0xj4J1xg.png")
        embed.add_field(name="Get help from the experts", value="Collaborate with our team of security experts and tap into the wealth of knowledge gained from hundreds of previous engagements", inline=False)
        embed.add_field(name="Gain clarity of your security event", value="Utilize threat intelligence to effectively allocate resources and make informed decisions based on the risks posed to your business", inline=False)
        embed.add_field(name="Get back to business faster", value="Get back on track quickly by taking immediate action to address the situation, minimize financial repercussions, and expedite the return to your core business operations", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/incident-response", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="pcoptimization", description="Learn more about PC Optimization", aliases=["opti"])
    async def pcoptimization(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's PC Optimization services

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/pc-optimization>)
        """
        embed = discord.Embed(title=f"PC Optimization", description=f"# Optimize system stability and performance\n\nRemove malware and stealers, update outdated system software and driver components, and know the condition of your hardware and expected repairs so you can get back to gaming faster", colour=16767334, url='https://www.beehive.systems/pc-optimization')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://asset.brandfetch.io/idGpYEfxfH/id0xj4J1xg.png")
        embed.add_field(name="Remove malware and potentially unwanted applications", value="Removing unused software and terminating threats can improve system resource accessibility", inline=False)
        embed.add_field(name="Know when hardware maintenance is required", value="Taking care of your PC and its operating conditions can improve hardware lifespan and operating performance", inline=False)
        embed.add_field(name="Increase gaming and streaming performance", value="A well-maintained PC will perform at its best capability for the longest, letting you do the most possible with it", inline=False)
        embed.add_field(name="Improve battery life and efficiency", value="A well optimized PC will leave more resources for you to utilize while playing, streaming, or working", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/pc-optimization", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True)
    @commands.group(name="serviceagent", description="Instructions to download and install the service agent", invoke_without_command=True)
    async def serviceagent(self, ctx: commands.Context):
        """
        Show an embed containing instructions to download and install the service agent for remote assistance
        """
        embed = discord.Embed(
            title="Download the BeeHive Service Agent",
            description="Before we can assist you remotely, you'll need to download and install our **Service Agent**.\n### We use this agent to...\n- **Remotely connect and control your device on request**\n- **Read diagnostic information about your device**\n- **Remotely orchestrate repairs and security operations**\n**and more...**\n\nWhile our software is installed on your system, information about you and your device, including any telemetry we collect, will be guarded subject to our **[Terms of Service](https://www.beehive.systems/tos)**, and **[Privacy Policy](https://www.beehive.systems/privacy)**.\n\nTo learn more about how we secure your private information, please visit our **[Trust Center](https://trust.beehive.systems)**",
            colour=16767334
        )
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.add_field(
            name="Instructions",
            value="**1.** Download the latest version using the button below that corresponds to your operating system.\n\n**2.** Run the downloaded file as administrator.\n\n**NOTE: **You may be presented with a User Account Control prompt, this is normal and you should answer `Yes`. The Service Agent will install silently and automatically. Once complete, you'll see a green globe in your taskbar, indicating a successful connection",
            inline=False
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="For Windows", url="https://cdn.beehive.systems/BeeHiveServiceAgent.msi", style=discord.ButtonStyle.link, emoji="<:windows:1194913113863114762>"))
        view.add_item(discord.ui.Button(label="Discord", url="https://discord.gg/ADz7YSegPT", style=discord.ButtonStyle.link))
        await ctx.send(embed=embed, view=view)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(name="win10", description="Show an embed warning the user about the incoming Windows 10 retirement", invoke_without_command=True)
    async def windows10alert(self, ctx: commands.Context):
        """
        Show an embed warning the user about the incoming Windows 10 retirement.
        """
        embed = discord.Embed(
            title="It's time to upgrade",
            description="**Microsoft has announced the end of support for Windows 10.**\nIt's important to upgrade to a newer version of Windows to continue receiving security updates and driver support.",
            colour=0xf8f9fb
        )
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/warning.png")
        embed.set_image(url="https://www.beehive.systems/hubfs/linkedmedia/timetoupgrade.png")
        embed.add_field(
            name="What does this mean?",
            value=f"When Windows 10 reaches it's **End of Life** (<t:1760400000:R>), all consumer Windows 10 versions will no longer receive security updates, leaving your system vulnerable to threats. Once support for Windows 10 itself is dropped, software and hardware manufacturers will gradually drop update support for systems still running Windows 10, which could lead to slowdowns, crashes, and missing features.",
            inline=False
        )
        embed.add_field(
            name="What should you do?",
            value="Consider upgrading to Windows 11 to ensure your device remains secure and operating at it's best capability. If your device isn't compatible with Windows 11, it might be time to upgrade your hardware to continue gaming for years to come.",
            inline=False
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Learn more", url="https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro", style=discord.ButtonStyle.link, emoji="🔗"))
        await ctx.send(embed=embed, view=view)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(name="reviewprompt", description="Prompt the user to leave a review about their experience", aliases=["reviewp"])
    async def reviewprompt(self, ctx: commands.Context):
        """
        Prompt the user to leave a review about their experience with BeeHive's services.
            
        Prefer to leave a review online?
        Choose one of the options below:
        """
        embed = discord.Embed(
            title="Got a second? Let us know how we're doing...",
            description="### We're working hard to provide high-quality CyberSecurity software and services to those who require it.\n\nIf you feel that your experience with BeeHive has been remarkable, please leave a review to help other customers discover us!",
            colour=16767334
        )
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/star-half.png")
        if ctx.guild and ctx.guild.id == 1147002526156206170:
            embed.add_field(
                name="In-Server Review",
                value="Use the `!review` command to leave a review directly in our server. This doesn't require an account and can be done in less than 10 seconds",
                inline=False
            )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="via our website", url="https://review.beehive.systems", style=discord.ButtonStyle.link, emoji="🔗"))
        view.add_item(discord.ui.Button(label="via HubSpot", url="https://app.hubspot.com/l/ecosystem/marketplace/solutions/beehive/write-review?eco_review_source=provider", style=discord.ButtonStyle.link, emoji="🔗"))
        await ctx.send(embed=embed, view=view)
