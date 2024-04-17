import contextlib
import datetime
import re
from typing import List
from urllib.parse import urlparse
import aiohttp
import discord
from discord.ext import tasks
from redbot.core import Config, commands, modlog
from redbot.core.bot import Red
from redbot.core.commands import Context

URL_REGEX_PATTERN = re.compile(
    r"^(?:http[s]?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
)


class AntiPhishing(commands.Cog):
    """
    Guard users from malicious links and phishing attempts with customizable protection options.
    """

    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=73835)
        self.config.register_guild(action="notify", caught=0)
        self.session = aiohttp.ClientSession()
        self.bot.loop.create_task(self.register_casetypes())
        self.bot.loop.create_task(self.get_phishing_domains())
        self.domains = []

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        return

    def format_help_for_context(self, ctx: Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    async def register_casetypes(self) -> None:
        with contextlib.suppress(RuntimeError):
            # notify setting
            await modlog.register_casetype(
                name="phish_found",
                default_setting=True,
                image="🎣",
                case_str="Malicious Link Detected",
            )
            # delete setting
            await modlog.register_casetype(
                name="phish_deleted",
                default_setting=True,
                image="🎣",
                case_str="Malicious Link Detected - Auto-Deleted",
            )
            # kick setting
            await modlog.register_casetype(
                name="phish_kicked",
                default_setting=True,
                image="🎣",
                case_str="Malicious Link Detected - Auto-Kicked",
            )
            # ban setting
            await modlog.register_casetype(
                name="phish_banned",
                default_setting=True,
                image="🎣",
                case_str="Malicious Link Detected - Auto-Banned",
            )

    @tasks.loop(minutes=10)
    async def get_phishing_domains(self) -> None:
        domains = []

        headers = {
            "X-Identity": f"BeeHive AntiPhishing v{self.__version__} (https://www.beehive.systems/sentri)",
        }

        async with self.session.get(
            "https://phish.sinking.yachts/v2/all", headers=headers
        ) as request:
            if request.status == 200:
                data = await request.json()
                domains.extend(data)

        async with self.session.get(
            "https://www.beehive.systems/hubfs/blocklist.json", headers=headers
        ) as request:
            if request.status == 200:
                data = await request.json()
                domains.extend(data)

        deduped = list(set(domains))
        self.domains = deduped

    def extract_urls(self, message: str) -> List[str]:
        """
        Extract URLs from a message.
        """
        # Find all regex matches
        matches = URL_REGEX_PATTERN.findall(message)
        return matches

    def get_links(self, message: str) -> List[str]:
        """
        Get links from the message content.
        """
        # Remove zero-width spaces
        message = message.replace("\u200b", "")
        message = message.replace("\u200c", "")
        message = message.replace("\u200d", "")
        message = message.replace("\u2060", "")
        message = message.replace("\uFEFF", "")
        if message != "":
            links = self.extract_urls(message)
            if not links:
                return
            return list(set(links))

    async def handle_phishing(self, message: discord.Message, domain: str) -> None:
        domain = domain[:250]
        action = await self.config.guild(message.guild).action()
        if not action == "ignore":
            count = await self.config.guild(message.guild).caught()
            await self.config.guild(message.guild).caught.set(count + 1)
        if action == "notify":
            if message.channel.permissions_for(message.guild.me).send_messages:
                with contextlib.suppress(discord.NotFound):
                    embed = discord.Embed(
                        title="Dangerous link detected!",
                        description=f"This message contains a malicious website or URL.\n\nThis URL could be anything from a fraudulent online seller, to an IP logger, to a page delivering malware intended to steal Discord accounts.\n\n**Don't click any links in this message, and notify server moderators ASAP**",
                        color=16729413,
                    )
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                    embed.timestamp = datetime.datetime.utcnow()
                    embed.set_footer(text="Link scanning powered by BeeHive",icon_url="")
                    await message.reply(embed=embed)
                    
                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.utcnow(),
                    action_type="phish_found",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a phishing link: {domain}",
                )
        elif action == "delete":
            if message.channel.permissions_for(message.guild.me).manage_messages:
                with contextlib.suppress(discord.NotFound):
                    await message.delete()

                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.utcnow(),
                    action_type="phish_deleted",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a phishing link: {domain}",
                )
        elif action == "kick":
            if (
                message.channel.permissions_for(message.guild.me).kick_members
                and message.channel.permissions_for(message.guild.me).manage_messages
            ):
                with contextlib.suppress(discord.NotFound):
                    await message.delete()
                    if (
                        message.author.top_role >= message.guild.me.top_role
                        or message.author == message.guild.owner
                    ):
                        return

                    await message.author.kick()

                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.utcnow(),
                    action_type="phish_kicked",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a phishing link: {domain}",
                )
        elif action == "ban":
            if (
                message.channel.permissions_for(message.guild.me).ban_members
                and message.channel.permissions_for(message.guild.me).manage_messages
            ):
                with contextlib.suppress(discord.NotFound):
                    await message.delete()
                    if (
                        message.author.top_role >= message.guild.me.top_role
                        or message.author == message.guild.owner
                    ):
                        return

                    await message.author.ban()

                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.utcnow(),
                    action_type="phish_banned",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a phishing link: {domain}",
                )

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        """
        Handles the logic for checking URLs.
        """

        if not message.guild or message.author.bot:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        links = self.get_links(message.content)
        if not links:
            return

        for url in links:
            domain = urlparse(url).netloc
            if domain in self.domains:
                await self.handle_phishing(message, domain)
                return

    @commands.command(
        aliases=["checkforphish", "checkscam", "checkforscam", "checkphishing"]
    )
    @commands.bot_has_permissions(embed_links=True)
    async def checkphish(self, ctx: Context, url: str = None):
        """
        Check if a url is a phishing scam.

        You can either provide a url or reply to a message containing a url.
        """
        if not url and not ctx.message.reference:
            return await ctx.send_help()

        if not url:
            try:
                m = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await ctx.send_help()
                return
            url = m.content

        url = url.strip("<>")
        urls = self.extract_urls(url)
        if not urls:
            embed = discord.Embed(title='Error: Invalid URL', description=f"You provided an invalid URL.\n\nCheck the formatting of any links and try again...", colour=16729413,)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
            await ctx.send(embed=embed)
            return

        real_url = urls[0]
        domain = urlparse(real_url).netloc

        if domain in self.domains:
            embed = discord.Embed(title="Link query: Detected!", description=f"**This is a known dangerous website!**\n\nThis website is blocklisted for malicious behavior or content.", colour=16729413,)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Link query: No detections", description=f"**This link looks clean.**\n\nYou should be able to proceed safely. Apply caution to your best judgement while browsing this site, and leave the site if at any time your sense of trust is impaired.", colour=2866574,)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
            await ctx.send(embed=embed)

    @commands.group(aliases=["antiphish"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def antiphishing(self, ctx: Context):
        """
        Settings to configure link safety in this server.
        """

    @antiphishing.command()
    async def action(self, ctx: Context, action: str):
        """
        Choose the action that occurs when a user sends a phishing scam.

        Options:
        `ignore` - Disables phishing protection
        `notify` - Alerts in channel when malicious links detected (default)
        `delete` - Deletes the message
        `kick` - Delete message and kick sender
        `ban` - Delete message and ban sender (recommended)
        """
        if action not in ["ignore", "notify", "delete", "kick", "ban"]:
            embed = discord.Embed(title='Error: Invalid action', description=f"You provided an invalid action. You are able to choose any of the following actions to occur when a malicious link is detected...\n\n`ignore` - Disables phishing protection\n`notify` - Alerts in channel when malicious links detected (default)\n`delete` - Deletes the message\n`kick` - Delete message and kick sender\n`ban` - Delete message and ban sender (recommended)\n\nRetry that command with one of the above options.", colour=16729413,)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
            await ctx.send(embed=embed)
            return

        await self.config.guild(ctx.guild).action.set(action)
        embed = discord.Embed(title='Settings changed', description=f"Malicious links will now trigger a **`{action}`** event when detected in chat.\n\nYou can make changes to this setting at any time.", colour=2866574,)
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
        await ctx.send(embed=embed)

    @antiphishing.command()
    async def stats(self, ctx: Context):
        """
        Shows the current stats for the anti-phishing integration.
        """
        caught = await self.config.guild(ctx.guild).caught()
        s = "s" if caught != 1 else ""
        embed = discord.Embed(title='Link protection statistics', description=f"I've caught and alerted to **`{caught}`** malicious link{s} since being added to this server.\n\nKeep me around to continue defending your community with protection powered by [**BeeHive's Comprehensive CyberThreat Intelligence**](<https://www.beehive.systems/>)", colour=16767334,)
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark-outline.png")
        await ctx.send(embed=embed)
