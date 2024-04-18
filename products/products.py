import asyncio
import time
import json
import io
import discord # type: ignore
from redbot.core import commands # type: ignore
from redbot.core import app_commands # type: ignore


class Products(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="antivirus", description="Learn more about BeeHive's AntiVirus", aliases=["av"])
    async def antivirus(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's AntiViral/AntiMalware software

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/antivirus>)
        """

        embed = discord.Embed(title=f"Award-winning protection against advanced online threats", description=f"# Protect your PC from malware and spyware in just a few clicks\n\n### BeeHive's security client is a security software application designed to protect users from malware or viruses while working, shopping, or playing games on their computers. It works by isolating unknown files in a safe virtual environment before performing real-time analysis to determine whether they pose any threat - all done without risk or alert fatigue for normal computer usage.", colour=16767334, url='https://www.beehive.systems/antivirus')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://i.imgur.com/NvGx5WK.png")
        embed.add_field(name="Real-Time AntiMalware", value="High-sensitivity file inspection occurs on-device to detect and block known and unknown malicious software", inline=False)
        embed.add_field(name="Real-Time AntiSpyware", value="Powerful protection from credential stealers, banking trojans, and other hard-to-detect infections", inline=False)
        embed.add_field(name="Intrusion Detection and Prevention", value="Analysis and blocking of potentially dangerous activities on the host device to preserve system integrity", inline=False)
        embed.add_field(name="Real-Time Cloud Analysis", value="Ongoing static and dynamic analysis of unknown objects within your filesystem for unidentified malware", inline=False)
        embed.add_field(name="Automated Threat Containment", value="Kernel-level API virtualization to monitor and contain unknowns during analysis and verdicting", inline=False)
        embed.add_field(name="Automated Remediation", value="No-touch, no-interaction, 100% hands free threat remediation across 7 layers of powerful protection", inline=False)
        embed.add_field(name="Start a 15 day free trial", value="Get 15 days of complete protection from malware, spyware, password stealers and more - no committment required. Subscribe today and cancel anytime from your billing dashboard.", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Start a 15 day free trial", url="https://buy.stripe.com/5kA8y62kIg06dLqdRc", style=discord.ButtonStyle.green, emoji="<:shield:1194906995036262420>"))
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/antivirus", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)
    
    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="vulnerabilityscanning", description="Learn more about Vulnerability Scanning")
    async def vulnerabilityscanning(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's Vulnerability Scanning and Monitoring services

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/vulnerability-scanning>)
        """
        embed = discord.Embed(title=f"Web vulnerability scanning and monitoring", description=f"# Scan and monitor for website and web application vulnerabilities\n\n### Hosting a website or web-app can cost a part-time job's worth of time to properly secure. Our Vulnerability Scanning and Vulnerability Monitoring makes it easier to know whether your changes and security mitigations are effective and help guide you on how to assume a better security posture over time.", colour=16767334, url='https://www.beehive.systems/vulnerability-scanning')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://i.imgur.com/rCRCEcP.png")
        embed.add_field(name="Know what's public", value="Discover and explore the full scope of visibility and vulnerabilities in your network, domain, or project with our detailed and carefully documented analysis. Our expert insights offer a comprehensive understanding of your system, enabling you to proactively address any potential weaknesses and bolster your defenses.", inline=False)
        embed.add_field(name="Find what's not supposed to be", value="Explore your platform's vulnerabilities, uncover hidden misconfigurations, identify vulnerable ports, and detect unpatched exploits. Our analysis equips you with the knowledge to fortify your platform's security and protect against potential threats.", inline=False)
        embed.add_field(name="Fix what's dangerous", value="Discover detailed, step-by-step instructions for effectively patching vulnerabilities and safeguarding your valuable information. Our comprehensive guides not only address weaknesses but also mitigate risks and bolster network security.", inline=False)
        embed.add_field(name="Verify it stays that way", value="Discover the power of observing the effects caused by modifications in your codebase and dependencies. Unleash the ability to effortlessly analyze and contrast different configurations spanning various domains or endpoints.", inline=False)
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
        embed = discord.Embed(title=f"Brand Protection", description=f"# Stop brand abuse before it starts\n\n### We offer automated and manual scanning, reviews, takedowns, and case management to keep your brand's identity on autopilot and stop brand abuse in it's tracks", colour=16767334, url='https://www.beehive.systems/brand-protection')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="")
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
        embed = discord.Embed(title=f"Incident Response", description=f"# Respond to potential cybersecurity incidents effectively\n\n### Detect and stop breaches, empower investigation, deploy defenses, and protect business continuity", colour=16767334, url='https://www.beehive.systems/incident-response')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="")
        embed.add_field(name="Get help from the experts", value="Collaborate with our team of security experts and tap into the wealth of knowledge gained from hundreds of previous engagements", inline=False)
        embed.add_field(name="Gain clarity of your security event", value="Utilize threat intelligence to effectively allocate resources and make informed decisions based on the risks posed to your business", inline=False)
        embed.add_field(name="Get back to business faster", value="Get back on track quickly by taking immediate action to address the situation, minimize financial repercussions, and expedite the return to your core business operations", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/incident-response", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)