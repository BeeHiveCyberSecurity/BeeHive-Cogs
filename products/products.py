import asyncio
import time
import json
import io
import discord
from redbot.core import commands
from redbot.core import app_commands


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

        embed = discord.Embed(title=f"Award-winning protection against advanced online threats", description=f"# Protect your PC from malware and spyware in just a few clicks\n\nBeeHive's security client is a security software application designed to protect users from malware or viruses while working, shopping, or playing games on their computers. It works by isolating unknown files in a safe virtual environment before performing real-time analysis to determine whether they pose any threat - all done without risk or alert fatigue for normal computer usage.", colour=16767334, url='https://www.beehive.systems/antivirus')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        embed.set_image(url="https://i.imgur.com/7i4Fr9O.png")
        embed.add_field(name="Real-Time AntiMalware", value="High-sensitivity file inspection occurs on-device to detect and block known and unknown malicious software", inline=True)
        embed.add_field(name="Real-Time AntiSpyware", value="Powerful protection from credential stealers, banking trojans, and other hard-to-detect infections", inline=True)
        embed.add_field(name="Intrusion Detection and Prevention", value="Analysis and blocking of potentially dangerous activities on the host device to preserve system integrity", inline=True)
        embed.add_field(name="Real-Time Cloud Analysis", value="Ongoing static and dynamic analysis of unknown objects within your filesystem for unidentified malware", inline=True)
        embed.add_field(name="Automated Threat Containment", value="Kernel-level API virtualization to monitor and contain unknowns during analysis and verdicting", inline=True)
        embed.add_field(name="Automated Remediation", value="No-touch, no-interaction, 100% hands free threat remediation across 7 layers of powerful protection", inline=True)
        embed.add_field(name="​", value="​", inline=False)
        embed.add_field(name="Start a 15 day free trial", value="Get 15 days of complete protection from malware, spyware, password stealers and more - no committment required. [**Subscribe today**](<https://buy.stripe.com/5kA8y62kIg06dLqdRc>), and cancel anytime from your billing portal.", inline=True)
        await ctx.send(embed=embed)
    
    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="vulnerabilityscanning", description="Learn more about Vulnerability Scanning", aliases=[""])
    async def vulnerabilityscanning(self, ctx: commands.Context):
        await ctx.send("vuln scanning test message")