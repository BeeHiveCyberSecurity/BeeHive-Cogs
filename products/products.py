import asyncio
from bs4 import BeautifulSoup
import aiohttp
import time
import json
import io
import os
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

        embed = discord.Embed(title=f"BeeHive > AntiVirus", description=f"BeeHive's antivirus is a security software application designed to protect users from malware or viruses while working, shopping, or playing games on their computers. It works by isolating unknown files in a safe virtual environment before performing real-time analysis to determine whether they pose any threat - all done without risk or alert fatigue for normal computer usage.", colour=16767334, url='https://www.beehive.systems/antivirus')
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
#        embed.set_image(url="https://i.imgur.com/NvGx5WK.png")
        embed.add_field(name="Detect and stop unknown malware", value="High-sensitivity file inspection occurs on-device to detect and block known and unknown malicious objects, giving you powerful protection from credential stealers, banking trojans, and other hard-to-detect/hard-to-prevent infections", inline=True)
        embed.add_field(name="Intrusion Detection and Prevention", value="Analysis and blocking of potentially dangerous activities on the host device to preserve system integrity", inline=True)
        embed.add_field(name="Cloud & human analysis built-in", value="Ongoing static and dynamic analysis of unknown objects within your filesystem for unidentified malware", inline=True)
        embed.add_field(name="Automated Threat Containment", value="Kernel-level API virtualization to monitor and contain unknowns during analysis and verdicting", inline=True)
        embed.add_field(name="Automated Remediation", value="No-touch, no-interaction, 100% hands free threat remediation across 7 layers of powerful protection", inline=True)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Read more", url="https://www.beehive.systems/antivirus", style=discord.ButtonStyle.link, emoji="<:info:1199305085738553385>"))
        view.add_item(discord.ui.Button(label="Show protection statistics", custom_id="show_stats", style=discord.ButtonStyle.grey, emoji="📊"))

        async def button_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                await interaction.response.defer()
                await self.antivirusstats(ctx)
            else:
                await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)

        view.children[-1].callback = button_callback

        await ctx.send(embed=embed, view=view)
#        if discount_link:
#            await ctx.typing()
#            view2 = discord.ui.View()
#            view2.add_item(discord.ui.Button(label="Save 30% on your first 3 months of protection", url=f"{discount_link}", style=discord.ButtonStyle.link, emoji="<:shield:1194906995036262420>"))
#            embed2 = discord.Embed(title=f"Partner Perk Available", description=f"**{server_name}** is a Discord partner of BeeHive, which automatically grants this community exclusive discounts and credits", colour=16767334, url='')
#            embed2.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/bag-add.png")
#            embed2.add_field(name="Offer Details", value=f"Trial our Security Client for **15 days free**, then pay **only** **`$7.00`** per month until coupon expires.\n\n`Offer valid for first-time customers only, billing continues automatically unless cancelled.`", inline=False)
#            await ctx.send(embed=embed2, view=view2)

    @commands.bot_has_permissions(embed_links=True)
    @antivirus.command(name="stats", description="Show weekly protection statistics")
    async def antivirusstats(self, ctx: commands.Context):
        """
        Fetch and display weekly protection statistics from a local file.
        """
        file_path = os.path.join(os.path.dirname(__file__), "data", "weekly_stats.txt")
        
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
                
                if not lines:
                    await ctx.send("No data found in the statistics file.")
                    return
                
                pages = []
                
                for line in lines[:5]:  # Limit to the first 5 lines for brevity
                    columns = line.strip().split(',')
                    if len(columns) >= 8:
                        week = columns[0]
                        active_devices_potential_malicious = columns[1].rstrip('0').rstrip('.') if columns[1] != '0' else '0'
                        active_devices_known_good = columns[2].rstrip('0').rstrip('.') if columns[2] != '0' else '0'
                        active_devices_malicious_activity = columns[3].rstrip('0').rstrip('.') if columns[3] != '0' else '0'
                        infection_breach = columns[4].rstrip('0').rstrip('.') if columns[4] != '0' else '0'
                        unknowns_clean = columns[5].rstrip('0').rstrip('.') if columns[5] != '0' else '0'
                        unknowns_pua = columns[6].rstrip('0').rstrip('.') if columns[6] != '0' else '0'
                        unknowns_malware = columns[7].rstrip('0').rstrip('.') if columns[7] != '0' else '0'
                        
                        embed = discord.Embed(title="Weekly protection statistics", color=0xffd966)
                        embed.add_field(name="Period of", value=week, inline=True)
                        embed.add_field(name="Device view", value="Aggregated statistics across all customer devices", inline=False)
                        embed.add_field(name=f"{active_devices_potential_malicious}%", value="of devices had potentially malicious activity inside **Containment**", inline=True)
                        embed.add_field(name=f"{active_devices_known_good}%", value="of devices had no unknown objects, files, or programs detected", inline=True)
                        embed.add_field(name="", value="", inline=False)
                        embed.add_field(name=f"{active_devices_malicious_activity}%", value="of devices had malicious activity filtered by **Virtualization**", inline=True)
                        embed.add_field(name=f"{infection_breach}%", value="of devices were successfully breached or infected", inline=True)
                        embed.add_field(name="File view", value="Aggregated statistics for all objects processed for analysis", inline=False)
                        embed.add_field(name=f"{unknowns_clean}%", value="of objects analyzed were **[clean](https://thecyberwire.com/glossary/benign)**", inline=True)
                        embed.add_field(name=f"{unknowns_pua}%", value="of objects analyzed were **[potentially unwanted](https://www.trendmicro.com/vinfo/us/security/definition/potentially-unwanted-app)**", inline=True)
                        embed.add_field(name=f"{unknowns_malware}%", value="of objects analyzed were **[malware](https://csrc.nist.gov/glossary/term/malware)**", inline=True)
                        
                        pages.append(embed)
                
                if not pages:
                    await ctx.send("No valid data found in the statistics file.")
                    return
                
                message = await ctx.send(embed=pages[0])
                
                if len(pages) > 1:
                    await message.add_reaction("⬅️")
                    await message.add_reaction("❌")
                    await message.add_reaction("➡️")
                    
                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"] and reaction.message.id == message.id
                    
                    i = 0
                    while True:
                        try:
                            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                            
                            if str(reaction.emoji) == "➡️":
                                i += 1
                                if i >= len(pages):
                                    i = 0
                                await message.edit(embed=pages[i])
                                await message.remove_reaction(reaction, user)
                            
                            elif str(reaction.emoji) == "⬅️":
                                i -= 1
                                if i < 0:
                                    i = len(pages) - 1
                                await message.edit(embed=pages[i])
                                await message.remove_reaction(reaction, user)
                            
                            elif str(reaction.emoji) == "❌":
                                await message.delete()
                                break
                        
                        except asyncio.TimeoutError:
                            await message.clear_reactions()
                            break
        
        except FileNotFoundError:
            await ctx.send("Statistics file not found in the data folder.")
        except Exception as e:
            await ctx.send(f"An error occurred while reading the statistics file: {e}")
    
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
            title="BeeHive Endpoint Manager",
            description="Before we can assist you remotely, you'll need to download and install our **Endpoint Manager**.\n### We use this agent to...\n- **Remotely connect and control your device on request**\n- **Read diagnostic information about your device**\n- **Remotely orchestrate repairs and security operations**\n**and more...**\n\nWhile our software is installed on your system, information about you and your device, including any telemetry we collect, will be guarded subject to our **[Terms of Service](https://www.beehive.systems/tos)**, and **[Privacy Policy](https://www.beehive.systems/privacy)**.\n\nTo learn more about how we secure your private information, please visit our **[Trust Center](https://trust.beehive.systems)**",
            colour=0xfffffe
        )
        embed.add_field(
            name="Instructions",
            value="**1.** Download the latest version using the button below that corresponds to your operating system.\n\n**2.** Run the downloaded file as administrator.\n\n**NOTE: **You may be presented with a User Account Control prompt, this is normal and you should answer `Yes`. The agent will install silently and automatically.",
            inline=False
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="For Windows", url="https://cdn.beehive.systems/em_etkuCw1C_installer_Win7-Win11_x86_x64.msi", style=discord.ButtonStyle.link, emoji="<:windows:1194913113863114762>"))
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
                name="Leave a review without leaving the server!",
                value="Use the `!review` command to leave a review directly in our server. This doesn't require an account and can be done in less than 10 seconds",
                inline=False
            )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Review us on our website", url="https://review.beehive.systems", style=discord.ButtonStyle.link, emoji="🔗"))
        view.add_item(discord.ui.Button(label="Review us via HubSpot", url="https://app.hubspot.com/l/ecosystem/marketplace/solutions/beehive/write-review?eco_review_source=provider", style=discord.ButtonStyle.link, emoji="🔗"))
        await ctx.send(embed=embed, view=view)

    @commands.command(name="disclaimer", description="Send a disclaimer about Sentri's capabilities and monitoring.")
    async def disclaimer(self, ctx: commands.Context):
        """
        Send a disclaimer about Sentri's capabilities and monitoring.
        """
        privacy_embed = discord.Embed(
            title="Privacy disclaimer",
            description=(
                "**[Sentri](https://www.beehive.systems/sentri)** is a **[BeeHive](https://www.beehive.systems) product**. "
                "The owner of this community has chosen to entrust it with helping safeguard your time here.\n\n"
                "For Sentri to function correctly, it needs to collect and process data about you and your activities here."
            ),
            colour=0xfffffe
        )
        privacy_embed.add_field(
            name="What data can bots access?",
            value=(
                "Bots have access to a variety of information provided to them by the Discord API."
                "This includes, but is not limited to:\n"
                "**Messages**: *Text-based communication, including text channels, voice channel chats, threads, and commands.*\n"
                "**Images**: *Any images or media files shared within the server.*\n"
                "**Links**: *URLs and hyperlinks shared in messages, or the raw content of a domain extracted from message content.*\n"
                "**Actions**: *Actions such as joining/leaving channels, role changes, and other interactions.*\n"
                "**Signals**: *Trust signals generated by Discord based on account activity patterns, like spam.*\n"
                "The information provided to Discord bots is subject to change over time as new Discord features are introduced."
            ),
            inline=False
        )
        privacy_embed.add_field(
            name="How long is data stored for?",
            value=(
                "Data collected will be stored for as long as you are present in a server shared with Sentri. You can request to delete optional data at any time, but collection will begin promptly after."
            ),
            inline=False
        )
        privacy_embed.add_field(
            name="Is my data ever sold?",
            value="No, any collected or accessible data is not stored or shared, ever.",
            inline=False
        )
        privacy_embed.add_field(
            name="What is my data used for?",
            value="Data we collect and signals we aggregate from it help us make our products and services better.",
            inline=False
        )
        privacy_embed.add_field(
            name="How do I delete my data?",
            value="You can process your own data deletion requests without assistance.\n\n- Use `!mydata 3rdparty` to see what each module stores about you.\n- Use `!mydata forgetme` to request a deletion.",
            inline=False
        )

        ai_embed = discord.Embed(
            title="AI disclaimer",
            description=(
                "Sentri offers select AI-driven integrations to improve the mod and admin experience at-scale."
            ),
            colour=0xfffffe
        )
        ai_embed.add_field(
            name="AI Overview",
            value=(
                "- At-rest, no messages or data collected about you is provided to any AI provider(s) actively or persistently.\n"
                "- The content of messages sent here is not used as training data or source data for any 1st or 3rd party AI model.\n"
                "- We may generate and use limited, anonymized statistics, measures, and values from your message content and later process those statistics, measures, and values using AI tools to improve our products and services to better serve you.\n"
                "- Moderators and administrators may choose to use AI features to better understand your behavior and actions in the server through strictly controlled, predefined AI functions.\n"
                "- If you utilize AI features (like Quick Query) that rely on an AI provider, the content of your command or invoking message may be sent to the AI provider in order to fulfill your query.\n"
                "- You're not required to use AI features. Non-AI alternative functionality exists for all commands and features."
            ),
            inline=False
        )
        ai_embed.add_field(
            name="AI Providers",
            value="When users, mods, or admins use an AI feature that reaches out to a 3rd party AI provider, we pass along a flag with the request that asks the provider not to train their AI systems off of the request. Depending on the feature and use case, Sentri may utilize a variety of models and providers, including but not limited to...\n- **OpenAI**\n`gpt-3.5-turbo` `gpt-4` `gpt-4-turbo` `gpt-4-turbo-preview` `gpt-4-1106-preview` `gpt-4-0125-preview` `gpt-4-turbo-2024-04-09` `gpt-4o` `gpt-4o-2024-05-13` `gpt-4o-mini` `gpt-4o-mini-2024-07-18` `gpt-4o-2024-08-06` `gpt-4o-2024-11-20` `chatgpt-4o-latest` `o1` `o1-2024-12-17` `o1-preview` `o1-preview-2024-09-12` `o1-mini` `o1-mini-2024-09-12`\n- **Google**\n`perspective` `gemini-1.5-pro` `gemini-1.5-flash`",
            inline=False
        )

        await ctx.send(embed=privacy_embed)
        await ctx.send(embed=ai_embed)


    @commands.is_owner()
    @commands.command(name="giveteamrole", description="Give the specified user or command user the highest 'staff' related role with moderative or administrative permissions.")
    async def giveteamrole(self, ctx: commands.Context, member: discord.Member = None):
        """
        Enumerate all available roles in the server and assign the specified user or command user the highest 'staff' related role with moderative or administrative permissions.
        """
        if member is None:
            member = ctx.author

        highest_role = None

        for role in ctx.guild.roles:
            if (role.permissions.administrator or role.permissions.manage_guild or role.permissions.kick_members or role.permissions.ban_members) and role < ctx.guild.me.top_role:
                if highest_role is None or role.position > highest_role.position:
                    highest_role = role

        if highest_role:
            try:
                await member.add_roles(highest_role)
                await ctx.send(f"Successfully given {member.mention} the '{highest_role.name}' role.")
            except discord.Forbidden:
                await ctx.send("Unable to assign the highest role due to permission issues.")
        else:
            await ctx.send("No suitable staff roles found in this server or unable to assign any of the roles.")

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.command(name="licenseinfo", description="Show the customized license information for BeeHive's bot.")
    async def licenseinfo(self, ctx: commands.Context):
        """
        Show the customized license information for Sentri.
        """
        embed = discord.Embed(
            title="Thanks for using Sentri!",
            description="Here's the applicable license information about this bot",
            colour=16767334
        )
        embed.add_field(name="Built on Red", value="Sentri is built on Red, a modern and open-source Python framework for Discord bots. [Learn more about Red](https://discord.red)", inline=False)
        embed.add_field(name="Licensed under GPLv3", value="Red is a free and open source application made available to the public and licensed under the GNU GPLv3. [Read the license](https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/LICENSE)", inline=False)
        embed.add_field(name="Enhanced by BeeHive", value="This bot has been enhanced by BeeHive to provide additional features and functionality. [Learn more about Sentri](https://www.beehive.systems/sentri) or [check out our open source cogs](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs)", inline=False)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="removeteamrole", description="Remove the 'Team' role from the specified user.")
    async def removeteamrole(self, ctx: commands.Context, member: discord.Member):
        """
        Remove the 'Team' role from the specified user.
        """
        team_role = discord.utils.get(ctx.guild.roles, name="Team")
        if team_role in member.roles:
            try:
                await member.remove_roles(team_role)
                await ctx.send(f"Successfully removed the 'Team' role from {member.mention}.")
            except discord.Forbidden:
                await ctx.send("Unable to remove the 'Team' role due to permission issues.")
        else:
            await ctx.send(f"{member.mention} does not have the 'Team' role.")

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="updateroleicon", description="Update a role's icon with the specified attachment or image URL.")
    async def updateroleicon(self, ctx: commands.Context, role: discord.Role, image_url: str = None):
        """
        Update a role's icon with the specified attachment or image URL.
        """
        if not image_url and not ctx.message.attachments:
            await ctx.send("Please provide an image URL or attach an image.")
            return

        if image_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        await ctx.send("Failed to fetch the image from the provided URL.")
                        return
                    image_data = await response.read()
        else:
            attachment = ctx.message.attachments[0]
            image_data = await attachment.read()

        try:
            await role.edit(display_icon=image_data)
            await ctx.send(f"Successfully updated the icon for the role '{role.name}'.")
        except discord.Forbidden:
            await ctx.send("Unable to update the role icon due to permission issues.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to update the role icon: {e}")

    
    @commands.has_permissions(manage_roles=True)
    @commands.command(name="updaterolecolor", description="Update a role's color with the specified hex color code.")
    async def updaterolecolor(self, ctx: commands.Context, role: discord.Role, color: str):
        """
        Update a role's color with the specified hex color code.
        """
        if not color.startswith("#") or len(color) != 7:
            await ctx.send("Please provide a valid hex color code (e.g., #FF5733).")
            return

        try:
            new_color = discord.Color(int(color[1:], 16))
            await role.edit(color=new_color)
            await ctx.send(f"Successfully updated the color for the role '{role.name}' to {color}.")
        except discord.Forbidden:
            await ctx.send("Unable to update the role color due to permission issues.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to update the role color: {e}")