import contextlib
import datetime
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import aiohttp  # type: ignore
import discord  # type: ignore
from discord.ext import tasks  # type: ignore
from redbot.core import Config, commands  # type: ignore
from redbot.core.bot import Red  # type: ignore
from redbot.core.commands import Context  # type: ignore
import tldextract

URL_REGEX_PATTERN = re.compile(
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,6}\b)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
)

class AntiPhishing(commands.Cog):
    """
    Guard users from malicious links and phishing attempts with customizable protection options.
    """

    __version__ = "1.6.4"
    __last_updated__ = "March 21, 2025"
    __quick_notes__ = "Bug fixes and improvements, alongside the removal of the (buggy) `scan` command"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=73836)
        self._initialize_config()
        self.session = aiohttp.ClientSession()
        self.domains = []
        self.domains_v2 = {}
        self.bot.loop.create_task(self.get_phishing_domains())

    def _initialize_config(self):
        self.config.register_guild(
            action="notify",
            caught=0,
            notifications=0,
            deletions=0,
            kicks=0,
            bans=0,
            timeouts=0,
            last_updated=None,
            log_channel=None,
            timeout_duration=30,  # Default timeout duration in minutes
            staff_role=None  # Configurable staff role mention
        )
        self.config.register_member(caught=0)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        return

    def format_help_for_context(self, ctx: Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nVersion {self.__version__}"
    
    def extract_urls(self, message: str) -> List[str]:
        """
        Extract URLs from a message.
        """
        return [match[0] for match in URL_REGEX_PATTERN.findall(message)]

    def get_links(self, message: str) -> Optional[List[str]]:
        """
        Get links from the message content.
        """
        zero_width_chars = ["\u200b", "\u200c", "\u200d", "\u2060", "\uFEFF"]
        for char in zero_width_chars:
            message = message.replace(char, "")
        if message:
            links = self.extract_urls(message)
            return list(set(links)) if links else None
        return None

    @commands.group()
    @commands.guild_only()
    async def antiphishing(self, ctx: Context):
        """
        Configurable options to help keep known malicious links out of your community's conversations.
        """

    @commands.admin_or_permissions()    
    @antiphishing.command()
    async def settings(self, ctx: Context):
        """
        Show current settings
        """
        guild_data = await self.config.guild(ctx.guild).all()
        embed = self._create_settings_embed(guild_data)
        await ctx.send(embed=embed)

    def _create_settings_embed(self, guild_data: dict) -> discord.Embed:
        log_channel_id = guild_data.get('log_channel', None)
        staff_role_id = guild_data.get('staff_role', None)
        log_channel_status = f"<#{log_channel_id}>" if log_channel_id else "Not Set"
        staff_role_status = f"<@&{staff_role_id}>" if staff_role_id else "Not Set"
        
        embed = discord.Embed(
            title='Current settings',
            colour=0xfffffe,
        )
        embed.add_field(name="Action", value=f"{guild_data.get('action', 'Not set').title()}", inline=False)
        embed.add_field(name="Log channel", value=log_channel_status, inline=False)
        embed.add_field(name="Staff Role", value=staff_role_status, inline=False)
        embed.add_field(name="Timeout Duration", value=f"{guild_data.get('timeout_duration', 30)} minutes", inline=False)
        return embed
        
    @commands.admin_or_permissions()
    @antiphishing.command()
    async def action(self, ctx: Context, action: str):
        """
        Customize enforcement

        Options:
        **`ignore`** - Disables phishing protection **(Not recommended)**
        **`notify`** - Alerts in channel when malicious links detected **(Default)**
        **`delete`** - Deletes the message silently
        **`kick`** - Deletes message and kicks sender
        **`ban`** - Deletes message and bans sender
        **`timeout`** - Delete message and temporarily time the user out **(Recommended)**
        """
        valid_actions = ["ignore", "notify", "delete", "kick", "ban", "timeout"]
        if action not in valid_actions:
            await self._send_invalid_action_embed(ctx)
            return

        await self.config.guild(ctx.guild).action.set(action)
        await self._send_action_confirmation(ctx, action)

    async def _send_invalid_action_embed(self, ctx: Context):
        await self._send_embed(
            ctx, 
            'Error: Invalid action', 
            "You provided an invalid action. You are able to choose any of the following actions to occur when a malicious link is detected...\n\n"
            "**`ignore`** - Disables phishing protection **(Not recommended)**\n"
            "**`notify`** - Alerts in channel when malicious links detected **(Default)**\n"
            "**`delete`** - Deletes the message\n"
            "**`kick`** - Delete message and kick sender\n"
            "**`ban`** - Delete message and ban sender\n"
            "**`timeout`** - Delete message and temporarily time the user out **(Recommended)**\n\n"
            "Retry that command with one of the above options.", 
            16729413, 
            "https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png"
        )

    async def _send_action_confirmation(self, ctx: Context, action: str):
        descriptions = {
            "ignore": "Phishing protection is now **disabled**. Malicious links will not trigger any actions.",
            "notify": "Malicious links will now trigger a **notification** in the channel when detected.",
            "delete": "Malicious links will now be **deleted** from conversation when detected.",
            "kick": "Malicious links will be **deleted** and the sender will be **kicked** when detected.",
            "ban": "Malicious links will be **deleted** and the sender will be **banned** when detected.",
            "timeout": "Malicious links will result in the user being **temporarily muted**."
        }
        colours = {
            "ignore": 0xffd966,  # Yellow
            "notify": 0xffd966,  # Yellow
            "delete": 0xff4545,  # Red
            "kick": 0xff4545,  # Red
            "ban": 0xff4545,  # Red
            "timeout": 0xffd966  # Yellow
        }
        
        thumbnail_urls = {
            "ignore": "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/close.png",
            "notify": "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/notifications.png",
            "delete": "https://www.beehive.systems/hubfs/Icon%20Packs/Red/trash.png",
            "kick": "https://www.beehive.systems/hubfs/Icon%20Packs/Red/footsteps.png",
            "ban": "https://www.beehive.systems/hubfs/Icon%20Packs/Red/ban.png",
            "timeout": "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/clock.png"
        }

        description = descriptions[action]
        colour = colours[action]
        thumbnail_url = thumbnail_urls[action]

        embed = discord.Embed(title='Settings changed', description=description, colour=colour)
        embed.set_thumbnail(url=thumbnail_url)
        await ctx.send(embed=embed)

    @antiphishing.command()
    async def stats(self, ctx: Context):
        """
        Check statistics
        """
        guild_data = await self.config.guild(ctx.guild).all()
        embed = self._create_stats_embed(guild_data)
        view = discord.ui.View()
        button = discord.ui.Button(label="Learn more about BeeHive", url="https://www.beehive.systems")
        view.add_item(button)
        await ctx.send(embed=embed, view=view)

    def _create_stats_embed(self, guild_data: dict) -> discord.Embed:
        caught, notifications, deletions, kicks, bans, timeouts = (
            guild_data.get('caught', 0),
            guild_data.get('notifications', 0),
            guild_data.get('deletions', 0),
            guild_data.get('kicks', 0),
            guild_data.get('bans', 0),
            guild_data.get('timeouts', 0)
        )
        total_domains = len(self.domains) + len(self.domains_v2)
        
        embed = discord.Embed(
            title='Link safety statistics', 
            colour=0xfffffe,
        )
        embed.add_field(name="Protection", value="", inline=False)
        embed.add_field(name="Detected", value=f"**{caught}** malicious link{'s' if caught != 1 else ''}", inline=True)
        embed.add_field(name="Notifications", value=f"Warned you of danger **{notifications}** time{'s' if notifications != 1 else ''}", inline=True)
        embed.add_field(name="Deletions", value=f"Removed **{deletions}** message{'s' if deletions != 1 else ''}", inline=True)
        embed.add_field(name="Kicks", value=f"Kicked **{kicks}** user{'s' if kicks != 1 else ''}", inline=True)
        embed.add_field(name="Bans", value=f"Banned **{bans}** user{'s' if bans != 1 else ''}", inline=True)
        embed.add_field(name="Timeouts", value=f"Timed out **{timeouts}** user{'s' if timeouts != 1 else ''}", inline=True)
        embed.add_field(name="Blocklist count", value=f"There are **{total_domains:,}** domains on the [BeeHive](https://www.beehive.systems) blocklist", inline=False)
        embed.add_field(name="About this cog", value="", inline=False)
        embed.add_field(name="Version", value=f"You're running **v{self.__version__}**", inline=True)
        embed.add_field(name="Last updated", value=f"**{self.__last_updated__}**", inline=True)
        embed.add_field(name="Recent changes", value=f"*{self.__quick_notes__}*", inline=False)
        return embed

    @commands.admin_or_permissions()
    @antiphishing.command()
    async def logchannel(self, ctx: Context, channel: discord.TextChannel):
        """
        Set logging channel
        """
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await self._send_embed(ctx, 'Settings changed', 
                               f"The logging channel has been set to {channel.mention}.", 
                               0x2bbd8e, "https://www.beehive.systems/hubfs/Icon%20Packs/Green/check-circle.png")

    @commands.admin_or_permissions()
    @antiphishing.command()
    async def staffrole(self, ctx: Context, role: discord.Role):
        """
        Set responder role
        """
        await self.config.guild(ctx.guild).staff_role.set(role.id)
        await self._send_embed(ctx, 'Settings changed', 
                               f"The staff role has been set to {role.mention}.", 
                               0x2bbd8e, "https://www.beehive.systems/hubfs/Icon%20Packs/Green/check-circle.png")

    @commands.admin_or_permissions()
    @antiphishing.command()
    async def timeoutduration(self, ctx: Context, minutes: int):
        """
        Set timeout duration
        """
        if minutes < 1:
            await self._send_embed(ctx, 'Error: Invalid duration', 
                                   "The timeout duration must be at least 1 minute.", 
                                   16729413, "https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            return

        await self.config.guild(ctx.guild).timeout_duration.set(minutes)
        await self._send_embed(ctx, 'Settings changed', 
                               f"The timeout duration is now set to **{minutes}** minutes.", 
                               0xffd966, "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/clock.png")

    @tasks.loop(minutes=15)
    async def get_phishing_domains(self) -> None:
        domains = set()
        domains_v2 = {}

        headers = {
            "X-Identity": f"BeeHive AntiPhishing v{self.__version__} (https://www.beehive.systems/)",
            "User-Agent": f"BeeHive AntiPhishing v{self.__version__} (https://www.beehive.systems/)"
        }

        await self._fetch_domains("https://www.beehive.systems/hubfs/blocklist/blocklist.json", headers, domains)
        await self._fetch_domains_v2("https://www.beehive.systems/hubfs/blocklist/blocklistv2.json", headers, domains_v2)

        self.domains = list(domains)
        self.domains_v2 = domains_v2

        # Send "Definitions updated" message to each individual log channel if set
        for guild in self.bot.guilds:
            log_channel_id = await self.config.guild(guild).log_channel()
            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="Definitions updated",
                        description="The phishing domains list has been updated.",
                        color=0x2bbd8e
                    )
                    await log_channel.send(embed=embed)

    async def _fetch_domains(self, url: str, headers: dict, domains: set):
        try:
            async with self.session.get(url, headers=headers) as request:
                if request.status == 200:
                    try:
                        data = await request.json()
                        if isinstance(data, list):
                            domains.update(data)
                        else:
                            print("Unexpected data format received from blocklist.")
                    except Exception as e:
                        print(f"Error parsing JSON from {url}: {e}")
                else:
                    print(f"Failed to fetch blocklist from {url}, status code: {request.status}")
        except aiohttp.ClientError as e:
            print(f"Network error while fetching blocklist from {url}: {e}")

    async def _fetch_domains_v2(self, url: str, headers: dict, domains_v2: Dict[str, Any]):
        try:
            async with self.session.get(url, headers=headers) as request:
                if request.status == 200:
                    try:
                        data = await request.json()
                        if isinstance(data, dict):
                            domains_v2.update(data)
                        else:
                            print("Unexpected data format received from blocklist v2.")
                    except Exception as e:
                        print(f"Error parsing JSON from {url}: {e}")
                else:
                    print(f"Failed to fetch blocklist v2 from {url}, status code: {request.status}")
        except aiohttp.ClientError as e:
            print(f"Network error while fetching blocklist v2 from {url}: {e}")

    async def follow_redirects(self, url: str) -> List[str]:
        """
        Follow redirects and return the final URL and any intermediate URLs.
        """
        urls = []
        headers = {
            "User-Agent": "BeeHive Security Intelligence (https://www.beehive.systems)"
        }
        try:
            async with self.session.head(url, allow_redirects=True, headers=headers) as response:
                urls.append(str(response.url))
                urls.extend(str(history.url) for history in response.history)
        except aiohttp.ClientError as e:
            print(f"Network error while following redirects: {e}")
        except Exception as e:
            print(f"Error following redirects: {e}")
        return urls

    async def handle_phishing(self, message: discord.Message, domain: str, redirect_chain: List[str]) -> None:
        domain = domain[:250]
        action = await self.config.guild(message.guild).action()
        if action != "ignore":
            count = await self.config.guild(message.guild).caught()
            await self.config.guild(message.guild).caught.set(count + 1)
        member_count = await self.config.member(message.author).caught()
        await self.config.member(message.author).caught.set(member_count + 1)
        
        log_channel_id = await self.config.guild(message.guild).log_channel()
        staff_role_id = await self.config.guild(message.guild).staff_role()
        if log_channel_id:
            log_channel = message.guild.get_channel(log_channel_id)
            if log_channel:
                await self._log_malicious_link(log_channel, message, domain, redirect_chain, staff_role_id)
        
        await self._take_action(action, message, domain, redirect_chain)

    async def _log_malicious_link(self, log_channel: discord.TextChannel, message: discord.Message, domain: str, redirect_chain: List[str], staff_role_id: Optional[int]):
        redirect_chain_str = "\n".join(redirect_chain)
        log_embed = discord.Embed(
            title="Malicious link detected",
            description=f"{message.author.mention} sent a dangerous link in {message.channel.mention}",
            color=0xff4545,
        )
        log_embed.add_field(name="User ID", value=f"```{message.author.id}```", inline=False)
        log_embed.add_field(name="Domain", value=f"```{domain}```", inline=False)
        log_embed.add_field(name="Redirects", value=f"```{redirect_chain_str}```", inline=False)
        
        # Add additional information if the domain is in the v2 list
        if domain in self.domains_v2:
            additional_info = self.domains_v2[domain]
            formatted_info = "\n".join(f"{key}: {value}" for key, value in additional_info.items())
            log_embed.add_field(name="Additional Info", value=f"```{formatted_info}```", inline=False)
        
        staff_mention = f"<@&{staff_role_id}>" if staff_role_id else ""
        await log_channel.send(content=staff_mention, embed=log_embed, allowed_mentions=discord.AllowedMentions(roles=True))

    async def _take_action(self, action: str, message: discord.Message, domain: str, redirect_chain: List[str]):
        action_methods = {
            "notify": self._notify_action,
            "delete": self._delete_action,
            "kick": self._kick_action,
            "ban": self._ban_action,
            "timeout": self._timeout_action
        }
        if action in action_methods:
            await action_methods[action](message, redirect_chain)

    async def _notify_action(self, message: discord.Message, redirect_chain: List[str]):
        if message.channel.permissions_for(message.guild.me).send_messages:
            with contextlib.suppress(discord.NotFound):
                mod_roles = await self.bot.get_mod_roles(message.guild)
                mod_mentions = " ".join(role.mention for role in mod_roles) if mod_roles else ""
                
                redirect_chain_status = self._get_redirect_chain_status(redirect_chain)
                
                embed = discord.Embed(
                    title="Dangerous link detected!",
                    description=(
                        f"This is a known malicious website. This website may contain malware or spyware, be a phishing lure, or otherwise attempt to convince you to hand over personal data or payment information. You should avoid visiting this website to safeguard your device and private information, and alert a staff member that this message appeared!"
                    ),
                    color=0xff4545,
                )
                embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning.png")
                embed.timestamp = datetime.datetime.utcnow()
                if mod_mentions:
                    await message.channel.send(content=mod_mentions, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
                else:
                    await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                
            notifications = await self.config.guild(message.guild).notifications()
            await self.config.guild(message.guild).notifications.set(notifications + 1)

    def _get_redirect_chain_status(self, redirect_chain: List[str]) -> List[str]:
        redirect_chain_status = []
        for url in redirect_chain:
            try:
                extracted = tldextract.extract(url)
                domain = f"{extracted.domain}.{extracted.suffix}"
                status = "Malicious" if domain in self.domains or domain in self.domains_v2 else "Unknown"
                redirect_chain_status.append(f"{url} ({status})")
            except IndexError:
                print(f"Error extracting domain from URL: {url}")
                redirect_chain_status.append(f"{url} (Unknown)")
        return redirect_chain_status

    async def _delete_action(self, message: discord.Message):
        if message.channel.permissions_for(message.guild.me).manage_messages:
            with contextlib.suppress(discord.NotFound):
                await message.delete()

            deletions = await self.config.guild(message.guild).deletions()
            await self.config.guild(message.guild).deletions.set(deletions + 1)

    async def _kick_action(self, message: discord.Message):
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

            kicks = await self.config.guild(message.guild).kicks()
            await self.config.guild(message.guild).kicks.set(kicks + 1)

    async def _ban_action(self, message: discord.Message):
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

            bans = await self.config.guild(message.guild).bans()
            await self.config.guild(message.guild).bans.set(bans + 1)

    async def _timeout_action(self, message: discord.Message):
        if message.channel.permissions_for(message.guild.me).moderate_members:
            with contextlib.suppress(discord.NotFound):
                await message.delete()
                if (
                    message.author.top_role >= message.guild.me.top_role
                    or message.author == message.guild.owner
                ):
                    return

                # Timeout the user for a customizable duration
                timeout_duration_minutes = await self.config.guild(message.guild).timeout_duration()
                timeout_duration = datetime.timedelta(minutes=timeout_duration_minutes)
                await message.author.timeout_for(timeout_duration, reason="Shared a known dangerous link")

            timeouts = await self.config.guild(message.guild).timeouts()  # Retrieve current timeout count
            await self.config.guild(message.guild).timeouts.set(timeouts + 1)  # Increment timeout count

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Handles the logic for checking URLs when a message is edited.
        """
        if not after.guild or after.author.bot:
            return
        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return

        links = self.get_links(after.content)
        if not links:
            return

        await self._process_links(after, links)

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

        await self._process_links(message, links)

    async def _process_links(self, message: discord.Message, links: List[str]):
        for url in links:
            domains_to_check = await self.follow_redirects(url)
            for domain_url in domains_to_check:
                extracted = tldextract.extract(domain_url)
                domain = f"{extracted.domain}.{extracted.suffix}".lower()  # Ensure domain comparison is case-insensitive
                if any(domain == blocked_domain.lower() for blocked_domain in self.domains + list(self.domains_v2.keys())):  # Compare against lowercased domains
                    await self.handle_phishing(message, domain, domains_to_check)
                    return




