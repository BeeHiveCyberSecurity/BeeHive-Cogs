import contextlib
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
import tldextract  # type: ignore
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
        self._initialize_config()
        self.session = aiohttp.ClientSession()
        self.domains = set()  # Stores lowercase registered domains
        self.domains_v2 = {}  # Stores lowercase registered domains -> additional info
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
        Extract URLs from a message using urlsplit for more robust parsing.
        Handles potential surrounding characters like < >
        """
        # Relaxed regex to find potential URLs, including those wrapped in <>
        # This regex aims to capture http/https URLs, potentially with surrounding characters.
        url_pattern = re.compile(r'(?:<)?(https?://[^\s<>]+)(?:>)?')
        urls = []
        # Remove zero-width characters first
        zero_width_chars = ["\u200b", "\u200c", "\u200d", "\u2060", "\uFEFF"]
        for char in zero_width_chars:
            message = message.replace(char, "")

        matches = url_pattern.finditer(message)
        for match in matches:
            url = match.group(1) # Get the captured URL part
            try:
                # Validate and reconstruct the URL to ensure it's well-formed
                result = urlsplit(url)
                if result.scheme in {"http", "https"} and result.netloc:
                    # Reconstruct to normalize (e.g., handle IDN domains, punycode)
                    reconstructed_url = urlunsplit(result)
                    urls.append(reconstructed_url)
                else:
                    log.debug(f"Skipping invalid URL structure: {url}")
            except ValueError as e:
                log.debug(f"Error parsing potential URL '{url}': {e}")
                continue
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
        action = action.lower() # Ensure action is lowercase
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
        colour = colours.get(action, 0xfffffe) # Default to white if action somehow invalid
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
        # Count unique domains from both lists
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

        if fetched_v1 or fetched_v2: # Only update if at least one fetch was successful
            # Check if the new data is different from the current data
            if new_domains != self.domains or new_domains_v2 != self.domains_v2:
                self.domains = new_domains
                self.domains_v2 = new_domains_v2
                updated = True
                log.info(f"Phishing domain lists updated. V1: {len(self.domains)} entries, V2: {len(self.domains_v2)} entries.")
            else:
                log.info("Phishing domain lists checked, no changes detected.")
        else:
            log.warning("Failed to fetch updates for both V1 and V2 blocklists.")
            return # Don't send update messages if fetching failed

        # Send "Definitions updated" message if lists were actually changed
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
                request.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
                try:
                    data = await request.json()
                    if isinstance(data, list):
                        # Store domains as lowercase
                        domains.update(d.lower() for d in data if isinstance(d, str))
                        log.debug(f"Successfully fetched and parsed V1 blocklist from {url}. {len(data)} entries raw.")
                        return True
                    else:
                        log.warning(f"Unexpected data format received from V1 blocklist {url}. Expected list, got {type(data)}.")
                        return False
                except aiohttp.ContentTypeError:
                    log.exception(f"Failed to decode JSON from V1 blocklist {url}. Content type: {request.content_type}")
                    return False
                except Exception as e:
                    log.exception(f"Error parsing JSON from V1 blocklist {url}: {e}")
                    return False
        except aiohttp.ClientResponseError as e:
            log.warning(f"HTTP error fetching V1 blocklist from {url}: {e.status} {e.message}")
            return False
        except aiohttp.ClientError as e:
            log.warning(f"Network error while fetching V1 blocklist from {url}: {e}")
            return False
        except Exception as e:
            log.exception(f"An unexpected error occurred fetching V1 blocklist from {url}: {e}")
            return False

    async def _fetch_domains_v2(self, url: str, headers: dict, domains_v2: Dict[str, Any]) -> bool:
        """Fetches V2 domain list, stores lowercase keys, returns True on success."""
        try:
            async with self.session.get(url, headers=headers, timeout=10) as request:
                request.raise_for_status()
                try:
                    data = await request.json()
                    if isinstance(data, dict):
                        # Store domain keys as lowercase
                        domains_v2.update({k.lower(): v for k, v in data.items() if isinstance(k, str)})
                        log.debug(f"Successfully fetched and parsed V2 blocklist from {url}. {len(data)} entries raw.")
                        return True
                    else:
                        log.warning(f"Unexpected data format received from V2 blocklist {url}. Expected dict, got {type(data)}.")
                        return False
                except aiohttp.ContentTypeError:
                    log.exception(f"Failed to decode JSON from V2 blocklist {url}. Content type: {request.content_type}")
                    return False
                except Exception as e:
                    log.exception(f"Error parsing JSON from V2 blocklist {url}: {e}")
                    return False
        except aiohttp.ClientResponseError as e:
            log.warning(f"HTTP error fetching V2 blocklist from {url}: {e.status} {e.message}")
            return False
        except aiohttp.ClientError as e:
            log.warning(f"Network error while fetching V2 blocklist from {url}: {e}")
            return False
        except Exception as e:
            log.exception(f"An unexpected error occurred fetching V2 blocklist from {url}: {e}")
            return False


    async def follow_redirects(self, url: str) -> List[str]:
        """
        Follow redirects using HEAD requests and return all unique URLs in the chain (lowercase hostnames).
        """
        visited_urls = set()
        redirect_chain = []
        current_url = url
        max_redirects = 10
        headers = {
            "User-Agent": f"BeeHive AntiPhishing v{self.__version__} (Discord Bot; +https://github.com/BeeHive-Systems/BeeHive-Cogs)"
        }

        for _ in range(max_redirects):
            if current_url in visited_urls:
                log.debug(f"Redirect loop detected for {url}, stopping at {current_url}")
                break # Avoid infinite loops
            visited_urls.add(current_url)

            try:
                # Use HEAD request to avoid downloading large content
                async with self.session.head(current_url, allow_redirects=False, headers=headers, timeout=5) as response:
                    # Add the current URL's hostname to the chain
                    try:
                        parsed = urlsplit(current_url)
                        if parsed.netloc:
                            redirect_chain.append(parsed.netloc.lower())
                    except ValueError:
                        log.warning(f"Could not parse URL for hostname: {current_url}")


                    # Check for redirect status codes (3xx)
                    if 300 <= response.status < 400:
                        next_url = response.headers.get('Location')
                        if not next_url:
                            log.warning(f"Redirect status {response.status} received from {current_url} but no Location header found.")
                            break # No location header to follow

                        # Handle relative redirects
                        next_url = urlunsplit(urlsplit(next_url)._replace(scheme=urlsplit(current_url).scheme) if not urlsplit(next_url).scheme else urlsplit(next_url))
                        current_url = next_url
                        log.debug(f"Following redirect from {response.url} to {current_url}")
                    else:
                        # Not a redirect, this is the final destination (or an error)
                        log.debug(f"Redirect chain for {url} ended at {current_url} with status {response.status}")
                        break
            except aiohttp.ClientResponseError as e:
                log.warning(f"HTTP error following redirects for {url} at step {current_url}: {e.status} {e.message}")
                # Add the hostname even if it errored, it might still be malicious
                try:
                    parsed = urlsplit(current_url)
                    if parsed.netloc:
                        redirect_chain.append(parsed.netloc.lower())
                except ValueError: pass
                break # Stop following on client/server errors
            except aiohttp.ClientError as e:
                log.warning(f"Network error following redirects for {url} at step {current_url}: {e}")
                break # Stop following on network errors
            except asyncio.TimeoutError:
                log.warning(f"Timeout following redirects for {url} at step {current_url}")
                break
            except Exception as e:
                log.exception(f"Unexpected error following redirects for {url} at step {current_url}: {e}")
                break
        else:
            log.warning(f"Reached maximum redirect limit ({max_redirects}) for {url}")
            # Add the last known hostname if max redirects reached
            try:
                parsed = urlsplit(current_url)
                if parsed.netloc:
                    redirect_chain.append(parsed.netloc.lower())
            except ValueError: pass

        # Return unique hostnames encountered
        return list(dict.fromkeys(redirect_chain)) # Preserves order while making unique


    async def handle_phishing(self, message: discord.Message, matched_domain: str, redirect_chain_hostnames: List[str]) -> None:
        """Handles the actions when a phishing link is detected."""
        log.info(f"Phishing link detected: '{matched_domain}' in message {message.id} by {message.author} ({message.author.id}) in guild {message.guild.id}. Redirect chain: {redirect_chain_hostnames}")
        action = await self.config.guild(message.guild).action()

        # Increment counters
        if action != "ignore":
            async with self.config.guild(message.guild).caught() as count:
                count += 1
        async with self.config.member(message.author).caught() as member_count:
            member_count += 1

        # Log the event
        log_channel_id = await self.config.guild(message.guild).log_channel()
        staff_role_id = await self.config.guild(message.guild).staff_role()
        if log_channel_id:
            log_channel = message.guild.get_channel(log_channel_id)
            if log_channel and log_channel.permissions_for(message.guild.me).send_messages:
                await self._log_malicious_link(log_channel, message, matched_domain, redirect_chain_hostnames, staff_role_id)
            elif log_channel:
                 log.warning(f"Missing permissions to log phishing detection in {log_channel.name} ({message.guild.name}).")
            else:
                 log.warning(f"Configured log channel {log_channel_id} not found in guild {message.guild.name} ({message.guild.id}).")


        # Take action
        await self._take_action(action, message, matched_domain, redirect_chain_hostnames)

    async def _log_malicious_link(self, log_channel: discord.TextChannel, message: discord.Message, matched_domain: str, redirect_chain_hostnames: List[str], staff_role_id: Optional[int]):
        """Sends a detailed log message to the designated channel."""
        redirect_chain_str = "\n".join(f"`{hostname}`" for hostname in redirect_chain_hostnames) if redirect_chain_hostnames else "`None`"
        # Truncate if too long for embed field
        if len(redirect_chain_str) > 1000:
            redirect_chain_str = redirect_chain_str[:1000] + "\n... (truncated)"

        log_embed = discord.Embed(
            title="🚨 Malicious Link Detected 🚨",
            description=f"{message.author.mention} (`{message.author.id}`) sent a dangerous link in {message.channel.mention}.",
            color=0xff4545, # Red
            timestamp=message.created_at
        )
        log_embed.set_author(name=f"{message.author.display_name} ({message.author.id})", icon_url=message.author.display_avatar.url)
        log_embed.add_field(name="Matched Domain", value=f"`{matched_domain}`", inline=False)
        log_embed.add_field(name="Full Message Content", value=f"```\n{message.content[:1000]}\n```" if message.content else "*(No text content)*", inline=False)
        log_embed.add_field(name="Redirect Chain (Hostnames)", value=redirect_chain_str, inline=False)
        log_embed.add_field(name="Action Taken", value=f"`{await self.config.guild(message.guild).action()}`", inline=True)
        log_embed.add_field(name="Message Link", value=f"[Jump to Message]({message.jump_url})", inline=True)

        # Add additional information if the domain is in the v2 list
        additional_info = self.domains_v2.get(matched_domain) # Use .get for safety
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


    async def _take_action(self, action: str, message: discord.Message, domain: str, redirect_chain: List[str]):
        """Executes the configured action."""
        action_methods = {
            "notify": self._notify_action,
            "delete": self._delete_action,
            "kick": self._kick_action,
            "ban": self._ban_action,
            "timeout": self._timeout_action,
            "ignore": None # Explicitly do nothing for ignore
        }
        if action in action_methods and action_methods[action]:
            # Check hierarchy before taking mod actions
            if action in ["kick", "ban", "timeout"]:
                 if isinstance(message.author, discord.Member): # Ensure it's a member object
                    # Cannot action owner or users with higher/equal roles than the bot
                    if message.author == message.guild.owner or message.author.top_role >= message.guild.me.top_role:
                        log.warning(f"Cannot perform '{action}' on {message.author} ({message.author.id}) due to hierarchy/ownership.")
                        # Fallback to delete if possible, otherwise notify
                        if await self._can_delete(message):
                            await self._delete_action(message, domain, redirect_chain, is_fallback=True)
                        elif await self._can_notify(message):
                             await self._notify_action(message, domain, redirect_chain, is_fallback=True)
                        return # Stop further action processing
                 else:
                     log.warning(f"Cannot perform '{action}' on {message.author} ({message.author.id}) as they are not a Member object (likely left?).")
                     # Fallback to delete if possible
                     if await self._can_delete(message):
                         await self._delete_action(message, domain, redirect_chain, is_fallback=True)
                     return # Stop further action processing


            await action_methods[action](message, domain, redirect_chain)
        elif action != "ignore":
            log.warning(f"Unknown action '{action}' configured for guild {message.guild.id}.")

    # --- Helper permission checks ---
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

    # --- Action Implementations ---

    async def _notify_action(self, message: discord.Message, domain: str, redirect_chain: List[str], is_fallback: bool = False):
        """Sends a warning message in the channel."""
        if not await self._can_notify(message):
            log.warning(f"Missing SEND_MESSAGES permission for notify action in {message.channel.name} ({message.guild.name}).")
            return

        try:
            # Fetch staff role for potential mention (use configured one if available)
            staff_role_id = await self.config.guild(message.guild).staff_role()
            staff_mention = f"<@&{staff_role_id}>" if staff_role_id else ""
            allowed_mentions = discord.AllowedMentions(roles=True if staff_role_id else False)

            embed = discord.Embed(
                title="🚨 Dangerous Link Detected! 🚨",
                description=(
                    f"{message.author.mention} sent a link (`{domain}`) identified as potentially malicious. "
                    "This website might contain malware, spyware, phishing attempts, or other harmful content. "
                    "**Avoid clicking this link.**"
                ),
                color=0xff4545, # Red
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning.png")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            embed.set_footer(text="Please alert staff if you believe this is an error.")

            # Add V2 info if available
            additional_info = self.domains_v2.get(domain)
            if additional_info and isinstance(additional_info, dict):
                formatted_info = "\n".join(f"**{key.replace('_', ' ').title()}**: {value}" for key, value in additional_info.items())
                if len(formatted_info) > 1000: formatted_info = formatted_info[:1000] + "\n... (truncated)"
                embed.add_field(name="Threat Details", value=formatted_info, inline=False)

            # Reply to the original message if possible, otherwise send to channel
            reply_target = message.to_reference(fail_if_not_exists=False)
            if reply_target:
                 await message.channel.send(content=staff_mention if staff_mention else None, embed=embed, allowed_mentions=allowed_mentions, reference=reply_target)
            else:
                 await message.channel.send(content=staff_mention if staff_mention else None, embed=embed, allowed_mentions=allowed_mentions)

            if not is_fallback: # Only count if it's the primary action
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


    async def _delete_action(self, message: discord.Message, domain: str, redirect_chain: List[str], is_fallback: bool = False):
        """Deletes the offending message."""
        if not await self._can_delete(message):
            log.warning(f"Missing MANAGE_MESSAGES permission for delete action in {message.channel.name} ({message.guild.name}).")
            # If delete fails as primary action, try to notify as fallback
            if not is_fallback and await self._can_notify(message):
                log.info("Falling back to notify action because delete failed due to permissions.")
                await self._notify_action(message, domain, redirect_chain, is_fallback=True)
            return

        try:
            await message.delete()
            log.info(f"Deleted message {message.id} due to phishing link '{domain}'.")
            if not is_fallback: # Only count if it's the primary action
                async with self.config.guild(message.guild).deletions() as count:
                    count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions to delete message {message.id}.")
            # If delete fails as primary action, try to notify as fallback
            if not is_fallback and await self._can_notify(message):
                log.info("Falling back to notify action because delete failed due to permissions.")
                await self._notify_action(message, domain, redirect_chain, is_fallback=True)
        except discord.NotFound:
            log.warning(f"Message {message.id} not found for deletion (already deleted?).")
        except discord.HTTPException as e:
            log.error(f"HTTP error deleting message {message.id}: {e}")
        except Exception as e:
            log.exception(f"Unexpected error during delete action: {e}")


    async def _kick_action(self, message: discord.Message, domain: str, redirect_chain: List[str]):
        """Deletes the message and kicks the user."""
        reason = f"Sent a known malicious link: {domain}"

        # Attempt delete first
        await self._delete_action(message, domain, redirect_chain, is_fallback=True) # Delete is part of kick

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


    async def _ban_action(self, message: discord.Message, domain: str, redirect_chain: List[str]):
        """Deletes the message and bans the user."""
        reason = f"Sent a known malicious link: {domain}"

        # Attempt delete first
        await self._delete_action(message, domain, redirect_chain, is_fallback=True) # Delete is part of ban

        if not await self._can_ban(message):
            log.warning(f"Missing BAN_MEMBERS permission for ban action in guild {message.guild.name}.")
            return

        if not isinstance(message.author, discord.Member): # Need member object to ban typically
             log.warning(f"Cannot ban {message.author} ({message.author.id}), not a member object.")
             # Could potentially ban by ID if needed, but requires different approach
             return

        try:
            # Ban with 0 days deletion, just ban the user
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


    async def _timeout_action(self, message: discord.Message, domain: str, redirect_chain: List[str]):
        """Deletes the message and times out the user."""
        reason = f"Sent a known malicious link: {domain}"

        # Attempt delete first
        await self._delete_action(message, domain, redirect_chain, is_fallback=True) # Delete is part of timeout

        if not await self._can_timeout(message):
            log.warning(f"Missing MODERATE_MEMBERS permission for timeout action in guild {message.guild.name}.")
            return

        if not isinstance(message.author, discord.Member):
             log.warning(f"Cannot timeout {message.author} ({message.author.id}), not a member object.")
             return

        try:
            timeout_duration_minutes = await self.config.guild(message.guild).timeout_duration()
            timeout_delta = datetime.timedelta(minutes=timeout_duration_minutes)

            # Use timeout method directly (available in recent d.py versions)
            await message.author.timeout(timeout_delta, reason=reason)

            log.info(f"Timed out {message.author} ({message.author.id}) for {timeout_duration_minutes} minutes. Reason: {reason}")
            async with self.config.guild(message.guild).timeouts() as count:
                count += 1
        except discord.Forbidden:
            log.warning(f"Missing permissions or hierarchy too low to timeout {message.author} ({message.author.id}).")
        except discord.HTTPException as e:
            # Handle specific error for timeout duration if needed (e.g., too long)
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
        # Ignore if content hasn't changed or if message is too old
        if before.content == after.content or (discord.utils.utcnow() - after.created_at).total_seconds() > 300:
             return
        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return
        # Check if user is immune based on permissions/roles (optional, add if needed)
        # if await self.is_immune(after.author):
        #     return

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
        # Check if user is immune based on permissions/roles (optional, add if needed)
        # if await self.is_immune(message.author):
        #     return

        links = self.get_links(message.content)
        if not links:
            return

        await self._process_links(message, links)

    async def _process_links(self, message: discord.Message, links: List[str]):
        """Processes extracted links, follows redirects, and checks against blocklists."""
        for url in links:
            log.debug(f"Processing link: {url} from message {message.id}")
            redirect_hostnames = await self.follow_redirects(url)
            log.debug(f"Redirect hostnames for {url}: {redirect_hostnames}")

            # Add the original URL's hostname if not already present from redirects
            try:
                original_hostname = urlsplit(url).netloc.lower()
                if original_hostname and original_hostname not in redirect_hostnames:
                    # Insert at the beginning for clarity
                    redirect_hostnames.insert(0, original_hostname)
            except ValueError:
                 log.warning(f"Could not parse original URL for hostname: {url}")


            for hostname in redirect_hostnames:
                # 1. Check exact hostname match (e.g., malicious.example.com)
                if hostname in self.domains or hostname in self.domains_v2:
                    log.debug(f"Exact match found: {hostname}")
                    await self.handle_phishing(message, hostname, redirect_hostnames)
                    return # Action taken, stop processing this message

                # 2. Check registered domain match (e.g., example.com from www.example.com)
                try:
                    # Use no_fetch=True as we don't need updated TLD list for every check
                    extracted = tldextract.extract(hostname, include_psl_private_domains=True)
                    # Construct registered domain only if both parts exist
                    if extracted.domain and extracted.suffix:
                        registered_domain = f"{extracted.domain}.{extracted.suffix}".lower()
                        # Avoid re-checking if hostname was already the registered domain
                        if registered_domain != hostname and (registered_domain in self.domains or registered_domain in self.domains_v2):
                            log.debug(f"Registered domain match found: {registered_domain} (from {hostname})")
                            await self.handle_phishing(message, registered_domain, redirect_hostnames)
                            return # Action taken, stop processing this message
                    # else:
                    #     log.debug(f"Could not extract registered domain from hostname: {hostname}")
                except Exception as e:
                    # Log error during extraction but continue checking other hostnames/links
                    log.error(f"Error extracting domain from hostname '{hostname}': {e}")
                    continue

            log.debug(f"No malicious domains found in chain for URL: {url}")




