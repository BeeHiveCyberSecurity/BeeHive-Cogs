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
        self.antivirus_links = {
            1147002526156206170: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",  # Example server ID and link
            1081164568669200384: "https://buy.stripe.com/5kA8y62kIg06dLqdRc?prefilled_promo_code=DIRTYTHR33&utm_source=discord&utm_medium=partnerperk",  # Another example server ID and link
            # Add more server IDs and their links as needed
        }

    @commands.guild_only()
    @commands.hybrid_group()
    async def product(self, ctx: commands.Context) -> None:
        """Product information related commands"""
        pass

    @commands.bot_has_permissions(embed_links=True)
    @product.command(name="antivirus", description="Learn more about BeeHive's AntiVirus", aliases=["av"])
    async def product_antivirus(self, ctx: commands.Context):
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
            await asyncio.sleep(3)
            view2 = discord.ui.View()
            view2.add_item(discord.ui.Button(label="Save 30% on your first 3 months of protection", url=f"{discount_link}", style=discord.ButtonStyle.link, emoji="<:shield:1194906995036262420>"))
            embed2 = discord.Embed(title=f"Partner Perk Available", description=f"**{server_name}** is a Discord partner of BeeHive, and this grants this community exclusive perks! Get an exclusive offer as thanks for your support of this server [here]({discount_link})", colour=16767334, url='https://www.beehive.systems/antivirus')
            embed2.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/bag-add.png")
            embed2.add_field(name="Offer Details", value=f"", inline=False)
            await ctx.send(embed=embed2, view=view2)
    
    @commands.bot_has_permissions(embed_links=True)
    @product.command(name="vulnerabilityscanning", description="Learn more about Vulnerability Scanning")
    async def product_vulnerabilityscanning(self, ctx: commands.Context):
        """
        Show an embed containing product details about BeeHive's Vulnerability Scanning and Monitoring services

        Prefer a website?
        Learn more [here](<https://www.beehive.systems/vulnerability-scanning>)
        """
        embed = discord.Embed(title=f"Vulnerability Scanning", description=f"# Scan and monitor for website and web application vulnerabilities\n\nHosting a website or web-app can cost a part-time job's worth of time to properly secure. Our Vulnerability Scanning and Vulnerability Monitoring makes it easier to know whether your changes and security mitigations are effective and help guide you on how to assume a better security posture over time.", colour=16767334, url='https://www.beehive.systems/vulnerability-scanning')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://asset.brandfetch.io/idGpYEfxfH/id0xj4J1xg.png")
        embed.add_field(name="Know what's public", value="Discover and explore the full scope of visibility and vulnerabilities in your network, domain, or project with our detailed and carefully documented analysis. Our expert insights offer a comprehensive understanding of your system, enabling you to proactively address any potential weaknesses and bolster your defenses.", inline=True)
        embed.add_field(name="Find what's not supposed to be", value="Explore your platform's vulnerabilities, uncover hidden misconfigurations, identify vulnerable ports, and detect unpatched exploits. Our analysis equips you with the knowledge to fortify your platform's security and protect against potential threats.", inline=True)
        embed.add_field(name="Fix what's dangerous", value="Discover detailed, step-by-step instructions for effectively patching vulnerabilities and safeguarding your valuable information. Our comprehensive guides not only address weaknesses but also mitigate risks and bolster network security.", inline=False)
        embed.add_field(name="Verify it stays that way", value="Discover the power of observing the effects caused by modifications in your codebase and dependencies. Unleash the ability to effortlessly analyze and contrast different configurations spanning various domains or endpoints.", inline=True)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Purchase a scan today", url="https://buy.stripe.com/14k8y64sQ15c4aQ4gg", style=discord.ButtonStyle.green, emoji="<:shield:1194906995036262420>"))
        view.add_item(discord.ui.Button(label="Learn more on our website", url="https://www.beehive.systems/vulnerability-scanning", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        await ctx.send(embed=embed, view=view)

    @commands.bot_has_permissions(embed_links=True)
    @product.command(name="brandprotection", description="Learn more about Brand Protection")
    async def product_brandprotection(self, ctx: commands.Context):
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
    @product.command(name="incidentresponse", description="Learn more about Incident Response", aliases=["ir"])
    async def product_incidentresponse(self, ctx: commands.Context):
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
    @product.command(name="pcoptimization", description="Learn more about PC Optimization", aliases=["opti"])
    async def product_pcoptimization(self, ctx: commands.Context):
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