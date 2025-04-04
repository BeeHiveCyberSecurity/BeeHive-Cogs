import asyncio
import datetime
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlsplit, urlunsplit
import aiohttp  # type: ignore
import discord  # type: ignore
from discord.ext import tasks  # type: ignore
from redbot.core import Config, commands  # type: ignore
from redbot.core.bot import Red  # type: ignore
from redbot.core.commands import Context  # type: ignore
import logging

log = logging.getLogger("red.beehive-cogs.antiphishing")

class AntiPhishing(commands.Cog):
    """
    Guard users from malicious links and phishing attempts with customizable protection options.
    """

    __version__ = "1.6.4" # TODO: Update version after changes
    __last_updated__ = "March 21, 2025" # TODO: Update date after changes
    __quick_notes__ = "Improved domain matching logic for better detection." # TODO: Update notes

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=73836)
        self.session = aiohttp.ClientSession()
        self.domains = set()  # Stores lowercase registered domains
        self.domains_v2 = {}  # Stores lowercase registered domains -> additional info
        self._initialize_config()
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
        self.get_phishing_domains.cancel() # Cancel the task loop

    async def red_delete_data_for_user(self, **kwargs):
        pass

    def format_help_for_context(self, ctx: Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nVersion {self.__version__}"

    def extract_urls(self, message: str) -> List[str]:
        """
        Extract URLs from a message using regex.
        Handles potential surrounding characters like < >
        """
        url_pattern = re.compile(r'(?:<)?(https?://[^\s<>]+)(?:>)?')
        zero_width_chars = ["\u200b", "\u200c", "\u200d", "\u2060", "\uFEFF"]
        for char in zero_width_chars:
            message = message.replace(char, "")

        matches = url_pattern.findall(message)
        urls = []
        for url in matches:
            try:
                result = urlsplit(url)
                if result.scheme in {"http", "https"} and result.netloc:
                    reconstructed_url = urlunsplit(result)
                    urls.append(reconstructed_url)
                else:
                    log.debug(f"Skipping invalid URL structure: {url}")
            except ValueError as e:
                log.debug(f"Error parsing potential URL '{url}': {e}")
        return urls

    def get_links(self, message: str) -> Optional[List[str]]:
        """
        Get unique links from the message content.
        """
        links = self.extract_urls(message)
        return list(set(links)) if links else None

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
        log_channel_id = guild_data.get('log_channel')
        staff_role_id = guild_data.get('staff_role')
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
        valid_actions = {"ignore", "notify", "delete", "kick", "ban", "timeout"}
        action = action.lower()
        if action not in valid_actions:
            await self._send_invalid_action_embed(ctx)
            return

        await self.config.guild(ctx.guild).action.set(action)
        await self._send_action_confirmation(ctx, action)

    async def _send_embed(self, ctx: Context, title: str, description: str, color: int, thumbnail_url: str):
        """Helper function to send consistent embeds."""
        embed = discord.Embed(title=title, description=description, colour=color)
        embed.set_thumbnail(url=thumbnail_url)
        await ctx.send(embed=embed)

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
            0xff4545, # Red color for error
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

        description = descriptions.get(action, "Unknown action configured.")
        colour = colours.get(action, 0xfffffe)
        thumbnail_url = thumbnail_urls.get(action, "")

        await self._send_embed(ctx, 'Settings changed', description, colour, thumbnail_url)

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
        total_domains = len(self.domains | set(self.domains_v2.keys()))

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
    async def logchannel(self, ctx: Context, channel: Optional[discord.TextChannel]):
        """
        Set or clear the logging channel. Provide no channel to clear.
        """
        if channel:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await self._send_embed(ctx, 'Settings changed',
                                   f"The logging channel has been set to {channel.mention}.",
                                   0x2bbd8e, "https://www.beehive.systems/hubfs/Icon%20Packs/Green/check-circle.png")
        else:
            await self.config.guild(ctx.guild).log_channel.clear()
            await self._send_embed(ctx, 'Settings changed',
                                   "The logging channel has been cleared.",
                                   0xffd966, "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/close.png")

    @commands.admin_or_permissions()
    @antiphishing.command()
    async def staffrole(self, ctx: Context, role: Optional[discord.Role]):
        """
        Set or clear the staff role to mention in logs. Provide no role to clear.
        """
        if role:
            await self.config.guild(ctx.guild).staff_role.set(role.id)
            await self._send_embed(ctx, 'Settings changed',
                                   f"The staff role has been set to {role.mention}.",
                                   0x2bbd8e, "https://www.beehive.systems/hubfs/Icon%20Packs/Green/check-circle.png")
        else:
            await self.config.guild(ctx.guild).staff_role.clear()
            await self._send_embed(ctx, 'Settings changed',
                                   "The staff role mention has been cleared.",
                                    0xffd966, "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/close.png")

    @commands.admin_or_permissions()
    @antiphishing.command()
    async def timeoutduration(self, ctx: Context, minutes: int):
        """
        Set timeout duration in minutes (minimum 1).
        """
        if minutes < 1:
            await self._send_embed(ctx, 'Error: Invalid duration',
                                   "The timeout duration must be at least 1 minute.",
                                   0xff4545, "https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            return

        await self.config.guild(ctx.guild).timeout_duration.set(minutes)
        await self._send_embed(ctx, 'Settings changed',
                               f"The timeout duration is now set to **{minutes}** minutes.",
                               0xffd966, "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/clock.png")

    @commands.admin_or_permissions()
    @antiphishing.command()
    async def lookup(self, ctx: Context, domain: str):
        """
        Lookup a domain in the blocklistv2 and show its details if it exists.
        """
        domain = domain.lower()
        if domain in self.domains_v2:
            additional_info = self.domains_v2[domain]
            formatted_info = "\n".join(f"**{key.replace('_', ' ').title()}**: {value}" for key, value in additional_info.items())
            embed = discord.Embed(
                title=f"Domain Lookup: {domain}",
                description=formatted_info,
                color=0x2bbd8e  # Green
            )
            await ctx.send(embed=embed)
        else:
            await self._send_embed(
                ctx,
                'Domain Not Found',
                f"The domain `{domain}` is not in the blocklistv2.",
                0xffd966,  # Yellow
                "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/close.png"
            )

    @tasks.loop(minutes=15)
    async def get_phishing_domains(self) -> None:
        """Fetches and updates the phishing domain lists."""
        log.info("Attempting to update phishing domain lists...")
        new_domains = set()
        new_domains_v2 = {}
        updated = False

        headers = {
            "X-Identity": f"BeeHive AntiPhishing v{self.__version__} (Discord Bot; +https://github.com/BeeHive-Systems/BeeHive-Cogs)",
            "User-Agent": f"BeeHive AntiPhishing v{self.__version__} (Discord Bot; +https://github.com/BeeHive-Systems/BeeHive-Cogs)"
        }

        # Fetch V1 list
        fetched_v1 = await self._fetch_domains("https://www.beehive.systems/hubfs/blocklist/blocklist.json", headers, new_domains)
        # Fetch V2 list
        fetched_v2 = await self._fetch_domains_v2("https://www.beehive.systems/hubfs/blocklist/blocklistv2.json", headers, new_domains_v2)

        if fetched_v1 or fetched_v2:
            if new_domains != self.domains or new_domains_v2 != self.domains_v2:
                self.domains = new_domains
                self.domains_v2 = new_domains_v2
                updated = True
                log.info(f"Phishing domain lists updated. V1: {len(self.domains)} entries, V2: {len(self.domains_v2)} entries.")
            else:
                log.info("Phishing domain lists checked, no changes detected.")
        else:
            log.warning("Failed to fetch updates for both V1 and V2 blocklists.")
            return

        if updated:
            for guild in self.bot.guilds:
                log_channel_id = await self.config.guild(guild).log_channel()
                if log_channel_id:
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel and log_channel.permissions_for(guild.me).send_messages:
                        try:
                            embed = discord.Embed(
                                title="Definitions updated",
                                description=f"The phishing domains list has been updated.\n"
                                            f"Now tracking **{len(self.domains) + len(self.domains_v2):,}** domains.",
                                color=0x2bbd8e # Green
                            )
                            await log_channel.send(embed=embed)
                        except discord.Forbidden:
                            log.warning(f"Missing permissions to send update message in {log_channel.name} ({guild.name}).")
                        except Exception as e:
                            log.error(f"Error sending update message to {log_channel.name} ({guild.name}): {e}")

    @get_phishing_domains.before_loop
    async def before_get_phishing_domains(self):
        await self.bot.wait_until_ready()
        log.info("Starting phishing domain update loop.")

    async def _fetch_domains(self, url: str, headers: dict, domains: set) -> bool:
        """Fetches V1 domain list, stores lowercase, returns True on success."""
        try:
            async with self.session.get(url, headers=headers, timeout=10) as request:
                request.raise_for_status()
                data = await request.json()
                if isinstance(data, list):
                    domains.update(d.lower() for d in data if isinstance(d, str))
                    log.debug(f"Successfully fetched and parsed V1 blocklist from {url}. {len(data)} entries raw.")
                    return True
                else:
                    log.warning(f"Unexpected data format received from V1 blocklist {url}. Expected list, got {type(data)}.")
                    return False
        except (aiohttp.ClientResponseError, aiohttp.ClientError) as e:
            log.warning(f"Error fetching V1 blocklist from {url}: {e}")
            return False
        except Exception as e:
            log.exception(f"An unexpected error occurred fetching V1 blocklist from {url}: {e}")
            return False

    async def _fetch_domains_v2(self, url: str, headers: dict, domains_v2: Dict[str, Any]) -> bool:
        """Fetches V2 domain list, stores lowercase keys, returns True on success."""
        try:
            async with self.session.get(url, headers=headers, timeout=10) as request:
                request.raise_for_status()
                data = await request.json()
                if isinstance(data, dict) and "blocklist" in data:
                    for entry in data["blocklist"]:
                        domain = entry.get("domain", "").lower()
                        if domain:
                            domains_v2[domain] = {
                                "category": entry.get("category", ""),
                                "severity": entry.get("severity", ""),
                                "description": entry.get("description", ""),
                                "targeted_orgs": entry.get("targeted_orgs", ""),
                                "detected_date": entry.get("detected_date", "")
                            }
                    log.debug(f"Successfully fetched and parsed V2 blocklist from {url}. {len(data['blocklist'])} entries raw.")
                    return True
                else:
                    log.warning(f"Unexpected data format received from V2 blocklist {url}. Expected dict with 'blocklist', got {type(data)}.")
                    return False
        except (aiohttp.ClientResponseError, aiohttp.ClientError) as e:
            log.warning(f"Error fetching V2 blocklist from {url}: {e}")
            return False
        except Exception as e:
            log.exception(f"An unexpected error occurred fetching V2 blocklist from {url}: {e}")
            return False

    async def handle_phishing(self, message: discord.Message, matched_domain: str) -> None:
        """Handles the actions when a phishing link is detected."""
        log.info(f"Phishing link detected: '{matched_domain}' in message {message.id} by {message.author} ({message.author.id}) in guild {message.guild.id}.")
        action = await self.config.guild(message.guild).action()

        if action != "ignore":
            async with self.config.guild(message.guild).caught() as count:
                count += 1
        async with self.config.member(message.author).caught() as member_count:
            member_count += 1

        log_channel_id = await self.config.guild(message.guild).log_channel()
        staff_role_id = await self.config.guild(message.guild).staff_role()
        if log_channel_id:
            log_channel = message.guild.get_channel(log_channel_id)
            if log_channel and log_channel.permissions_for(message.guild.me).send_messages:
                await self._log_malicious_link(log_channel, message, matched_domain, staff_role_id)
            elif log_channel:
                log.warning(f"Missing permissions to log phishing detection in {log_channel.name} ({message.guild.name}).")
            else:
                log.warning(f"Configured log channel {log_channel_id} not found in guild {message.guild.name} ({message.guild.id}).")

        await self._take_action(action, message, matched_domain)

    async def _log_malicious_link(self, log_channel: discord.TextChannel, message: discord.Message, matched_domain: str, staff_role_id: Optional[int]):
        """Sends a detailed log message to the designated channel."""
        log_embed = discord.Embed(
            title="🚨 Malicious Link Detected 🚨",
            description=f"{message.author.mention} (`{message.author.id}`) sent a dangerous link in {message.channel.mention}.",
            color=0xff4545, # Red
            timestamp=message.created_at
        )
        log_embed.set_author(name=f"{message.author.display_name} ({message.author.id})", icon_url=message.author.display_avatar.url)
        log_embed.add_field(name="Matched Domain", value=f"`{matched_domain}`", inline=False)
        log_embed.add_field(name="Full Message Content", value=f"```\n{message.content[:1000]}\n```" if message.content else "*(No text content)*", inline=False)
        log_embed.add_field(name="Action Taken", value=f"`{await self.config.guild(message.guild).action()}`", inline=True)
        log_embed.add_field(name="Message Link", value=f"[Jump to Message]({message.jump_url})", inline=True)

        additional_info = self.domains_v2.get(matched_domain)
        if additional_info and isinstance(additional_info, dict):
            try:
                formatted_info = "\n".join(f"**{key.replace('_', ' ').title()}**: {value}" for key, value in additional_info.items())
                if len(formatted_info) > 1000:
                    formatted_info = formatted_info[:1000] + "\n... (truncated)"
                log_embed.add_field(name="Additional Info (V2)", value=formatted_info, inline=False)
            except Exception as e:
                log.error(f"Error formatting V2 additional info for log: {e}")

        log_embed.set_footer(text=f"User total detections: {await self.config.member(message.author).caught()}")

        staff_mention = f"<@&{staff_role_id}>" if staff_role_id else ""
        allowed_mentions = discord.AllowedMentions(roles=True if staff_role_id else False)

        try:
            await log_channel.send(content=staff_mention if staff_mention else None, embed=log_embed, allowed_mentions=allowed_mentions)
        except discord.Forbidden:
            log.warning(f"Missing permissions to send log embed in {log_channel.name} ({log_channel.guild.name}).")
        except discord.HTTPException as e:
            log.error(f"HTTP error sending log embed in {log_channel.name} ({log_channel.guild.name}): {e}")
        except Exception as e:
            log.exception(f"Unexpected error sending log embed: {e}")

    async def _take_action(self, action: str, message: discord.Message, domain: str):
        """Executes the configured action."""
        action_methods = {
            "notify": self._notify_action,
            "delete": self._delete_action,
            "kick": self._kick_action,
            "ban": self._ban_action,
            "timeout": self._timeout_action,
            "ignore": None
        }
        if action in action_methods and action_methods[action]:
            if action in ["kick", "ban", "timeout"]:
                if isinstance(message.author, discord.Member):
                    if message.author == message.guild.owner or message.author.top_role >= message.guild.me.top_role:
                        log.warning(f"Cannot perform '{action}' on {message.author} ({message.author.id}) due to hierarchy/ownership.")
                        if await self._can_delete(message):
                            await self._delete_action(message, domain, is_fallback=True)
                        elif await self._can_notify(message):
                            await self._notify_action(message, domain, is_fallback=True)
                        return
                else:
                    log.warning(f"Cannot perform '{action}' on {message.author} ({message.author.id}) as they are not a Member object (likely left?).")
                    if await self._can_delete(message):
                        await self._delete_action(message, domain, is_fallback=True)
                    return

            await action_methods[action](message, domain)
        elif action != "ignore":
            log.warning(f"Unknown action '{action}' configured for guild {message.guild.id}.")

    async def _can_notify(self, message: discord.Message) -> bool:
        return message.channel.permissions_for(message.guild.me).send_messages

    async def _can_delete(self, message: discord.Message) -> bool:
        return message.channel.permissions_for(message.guild.me).manage_messages

    async def _can_kick(self, message: discord.Message) -> bool:
        return message.guild.me.guild_permissions.kick_members

    async def _can_ban(self, message: discord.Message) -> bool:
        return message.guild.me.guild_permissions.ban_members

    async def _can_timeout(self, message: discord.Message) -> bool:
        return message.guild.me.guild_permissions.moderate_members

    async def _notify_action(self, message: discord.Message, domain: str, is_fallback: bool = False):
        """Sends a warning message in the channel."""
        if not await self._can_notify(message):
            log.warning(f"Missing SEND_MESSAGES permission for notify action in {message.channel.name} ({message.guild.name}).")
            return

        try:
            staff_role_id = await self.config.guild(message.guild).staff_role()
            staff_mention = f"<@&{staff_role_id}>" if staff_role_id else ""
            allowed_mentions = discord.AllowedMentions(roles=True if staff_role_id else False)

            embed = discord.Embed(
                title="🚨 Dangerous link detected",
                color=0xff4545, # Red
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning.png")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            embed.set_footer(text="Please alert staff if you believe this is an error.")

            additional_info = self.domains_v2.get(domain)
            if additional_info and isinstance(additional_info, dict):
                description = (
                    f"{message.author.mention} sent a link (`{domain}`) identified as potentially malicious. "
                    "This website might contain malware, spyware, phishing attempts, or other harmful content. "
                    "**Avoid clicking this link.**\n\n"
                    f"**Category**: {additional_info.get('category', 'N/A')}\n"
                    f"**Description**: {additional_info.get('description', 'N/A')}\n"
                    f"**Targeted Organizations**: {additional_info.get('targeted_orgs', 'N/A')}\n"
                    f"**Detected Date**: {additional_info.get('detected_date', 'N/A')}"
                )
                embed.add_field(name="Threat Details", value=description, inline=False)
            else:
                embed.description = (
                    f"{message.author.mention} sent a link (`{domain}`) identified as potentially malicious. "
                    "This website might contain malware, spyware, phishing attempts, or other harmful content. "
                    "**Avoid clicking this link.**"
                )

            reply_target = message.to_reference(fail_if_not_exists=False)
            if reply_target:
                await message.channel.send(content=staff_mention if staff_mention else None, embed=embed, allowed_mentions=allowed_mentions, reference=reply_target)
            else:
                await message.channel.send(content=staff_mention if staff_mention else None, embed=embed, allowed_mentions=allowed_mentions)

            if not is_fallback:
                async with self.config.guild(message.guild).notifications() as count:
                    count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions for notify action (reply/send) in {message.channel.name} ({message.guild.name}).")
        except discord.NotFound:
            log.warning(f"Original message {message.id} not found for notify action.")
        except discord.HTTPException as e:
            log.error(f"HTTP error during notify action for message {message.id}: {e}")
        except Exception as e:
            log.exception(f"Unexpected error during notify action: {e}")

    async def _delete_action(self, message: discord.Message, domain: str, is_fallback: bool = False):
        """Deletes the offending message."""
        if not await self._can_delete(message):
            log.warning(f"Missing MANAGE_MESSAGES permission for delete action in {message.channel.name} ({message.guild.name}).")
            if not is_fallback and await self._can_notify(message):
                log.info("Falling back to notify action because delete failed due to permissions.")
                await self._notify_action(message, domain, is_fallback=True)
            return

        try:
            await message.delete()
            log.info(f"Deleted message {message.id} due to phishing link '{domain}'.")
            if not is_fallback:
                async with self.config.guild(message.guild).deletions() as count:
                    count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions to delete message {message.id}.")
            if not is_fallback and await self._can_notify(message):
                log.info("Falling back to notify action because delete failed due to permissions.")
                await self._notify_action(message, domain, is_fallback=True)
        except discord.NotFound:
            log.warning(f"Message {message.id} not found for deletion (already deleted?).")
        except discord.HTTPException as e:
            log.error(f"HTTP error deleting message {message.id}: {e}")
        except Exception as e:
            log.exception(f"Unexpected error during delete action: {e}")

    async def _kick_action(self, message: discord.Message, domain: str):
        """Deletes the message and kicks the user."""
        reason = f"Sent a known malicious link: {domain}"

        await self._delete_action(message, domain, is_fallback=True)

        if not await self._can_kick(message):
            log.warning(f"Missing KICK_MEMBERS permission for kick action in guild {message.guild.name}.")
            return

        if not isinstance(message.author, discord.Member):
            log.warning(f"Cannot kick {message.author} ({message.author.id}), not a member object.")
            return

        try:
            await message.author.kick(reason=reason)
            log.info(f"Kicked {message.author} ({message.author.id}) for reason: {reason}")
            async with self.config.guild(message.guild).kicks() as count:
                count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions or hierarchy too low to kick {message.author} ({message.author.id}).")
        except discord.HTTPException as e:
            log.error(f"HTTP error kicking {message.author} ({message.author.id}): {e}")
        except Exception as e:
            log.exception(f"Unexpected error during kick action: {e}")

    async def _ban_action(self, message: discord.Message, domain: str):
        """Deletes the message and bans the user."""
        reason = f"Sent a known malicious link: {domain}"

        await self._delete_action(message, domain, is_fallback=True)

        if not await self._can_ban(message):
            log.warning(f"Missing BAN_MEMBERS permission for ban action in guild {message.guild.name}.")
            return

        if not isinstance(message.author, discord.Member):
            log.warning(f"Cannot ban {message.author} ({message.author.id}), not a member object.")
            return

        try:
            await message.author.ban(reason=reason, delete_message_days=0)
            log.info(f"Banned {message.author} ({message.author.id}) for reason: {reason}")
            async with self.config.guild(message.guild).bans() as count:
                count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions or hierarchy too low to ban {message.author} ({message.author.id}).")
        except discord.HTTPException as e:
            log.error(f"HTTP error banning {message.author} ({message.author.id}): {e}")
        except Exception as e:
            log.exception(f"Unexpected error during ban action: {e}")

    async def _timeout_action(self, message: discord.Message, domain: str):
        """Deletes the message and times out the user."""
        reason = f"Sent a known malicious link: {domain}"

        await self._delete_action(message, domain, is_fallback=True)

        if not await self._can_timeout(message):
            log.warning(f"Missing MODERATE_MEMBERS permission for timeout action in guild {message.guild.name}.")
            return

        if not isinstance(message.author, discord.Member):
            log.warning(f"Cannot timeout {message.author} ({message.author.id}), not a member object.")
            return

        try:
            timeout_duration_minutes = await self.config.guild(message.guild).timeout_duration()
            timeout_delta = datetime.timedelta(minutes=timeout_duration_minutes)

            await message.author.timeout(timeout_delta, reason=reason)

            log.info(f"Timed out {message.author} ({message.author.id}) for {timeout_duration_minutes} minutes. Reason: {reason}")
            async with self.config.guild(message.guild).timeouts() as count:
                count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions or hierarchy too low to timeout {message.author} ({message.author.id}).")
        except discord.HTTPException as e:
            log.error(f"HTTP error timing out {message.author} ({message.author.id}): {e}")
        except Exception as e:
            log.exception(f"Unexpected error during timeout action: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Handles the logic for checking URLs when a message is edited.
        Ignores messages older than 5 minutes to avoid unnecessary checks.
        """
        if not after.guild or after.author.bot:
            return
        if before.content == after.content or (discord.utils.utcnow() - after.created_at).total_seconds() > 300:
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
        Handles the logic for checking URLs in new messages.
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
        """Processes extracted links and checks against blocklists."""
        for url in links:
            log.debug(f"Processing link: {url} from message {message.id}")

            try:
                hostname = urlsplit(url).netloc.lower()
            except ValueError:
                log.warning(f"Could not parse URL for hostname: {url}")
                continue

            if hostname in self.domains or hostname in self.domains_v2:
                log.debug(f"Exact match found: {hostname}")
                await self.handle_phishing(message, hostname)
                continue

            try:
                domain_match = re.search(r'([a-z0-9-]+\.[a-z]{2,})$', hostname)
                if domain_match:
                    registered_domain = domain_match.group(1).lower()
                    if registered_domain != hostname and (registered_domain in self.domains or registered_domain in self.domains_v2):
                        log.debug(f"Registered domain match found: {registered_domain} (from {hostname})")
                        await self.handle_phishing(message, registered_domain)
                        continue
            except Exception as e:
                log.error(f"Error extracting domain from hostname '{hostname}': {e}")
                continue

            log.debug(f"No malicious domains found for URL: {url}")




