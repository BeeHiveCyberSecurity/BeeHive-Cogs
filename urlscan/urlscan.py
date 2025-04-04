import aiohttp  # type: ignore
import asyncio
import discord  # type: ignore
import json
import re
from redbot.core import commands  # type: ignore
from redbot.core import app_commands  # type: ignore
from redbot.core import Config  # type: ignore


class URLScan(commands.Cog):
    """URLScan file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "autoscan_enabled": False,
            "log_channel": None
        }
        self.config.register_guild(**default_guild)

    @commands.group(name='urlscan', help="Scan URL's for dangerous content", invoke_without_command=True)
    async def urlscan(self, ctx):
        """Base command for URLScan. Use subcommands for specific actions."""
        await ctx.send_help(ctx.command)

    @urlscan.command(name='scan', help="Scan a URL using urlscan.io")
    async def scan(self, ctx, *, urls: str = None):
        """Scan a URL using urlscan.io"""
        await self.scan_urls(ctx, urls)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @urlscan.command(name="autoscan", description="Toggle automatic URL scanning")
    async def autoscan(self, ctx, state: bool = None):
        """Toggle automatic URL scanning in messages"""
        if state is None:
            state = await self.config.guild(ctx.guild).autoscan_enabled()
            embed = discord.Embed(
                title="URLScan Status",
                description=f"Automatic URL scanning is currently {'enabled' if state else 'disabled'}.",
                color=0x2BBD8E if state else 0xff4545
            )
            await ctx.send(embed=embed)
        else:
            await self.config.guild(ctx.guild).autoscan_enabled.set(state)
            embed = discord.Embed(
                title="URLScan Status",
                description=f"Automatic URL scanning has been {'enabled' if state else 'disabled'}.",
                color=0x2BBD8E if state else 0xff4545
            )
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @urlscan.command(name="logs", description="Set the logging channel")
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the logging channel for URL scan results"""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    async def scan_urls(self, ctx, urls: str = None):
        urlscan_key = await self.bot.get_shared_api_tokens("urlscan")
        api_key = urlscan_key.get("api_key")
        if api_key is None:
            await ctx.send("The URLScan API key has not been set.")
            return

        if urls is None:
            if ctx.message.reference and ctx.message.reference.resolved:
                ref_msg = ctx.message.reference.resolved
                urls = ref_msg.content
            else:
                await ctx.send("Please provide a URL or reply to a message with URLs!")
                return

        urls_to_scan = re.findall(r'(https?://\S+)', urls)
        if not urls_to_scan:
            await ctx.send("No valid URLs found to scan.")
            return

        headers = {
            "Content-Type": "application/json",
            "API-Key": api_key
        }

        async with aiohttp.ClientSession() as session:
            for url in urls_to_scan:
                data = {"url": url, "visibility": "public"}
                try:
                    async with ctx.typing():
                        async with session.post('https://urlscan.io/api/v1/scan/', headers=headers, json=data, timeout=10) as r:
                            res = await r.json()
                            if 'result' not in res:
                                await ctx.send(f"{res.get('message', 'Unknown error')}")
                                continue

                            report_url = res['result']
                            report_api = res['api']
                            await asyncio.sleep(30)
                            async with session.get(report_api, timeout=10) as r2:
                                res2 = await r2.json()
                                view = discord.ui.View()

                                embed = discord.Embed()
                                if 'verdicts' in res2 and 'overall' in res2['verdicts'] and 'score' in res2['verdicts']['overall']:
                                    threat_level = res2['verdicts']['overall']['score']
                                    if threat_level != 0:
                                        embed.title = "URLscan.io is suspicious"
                                        embed.description = f"URLScan says {url} is suspicious!\n\nFor your own safety, please don't click it."
                                        embed.color = 0xe25946
                                        view.add_item(discord.ui.Button(label="View results", url=report_url, style=discord.ButtonStyle.link))
                                    else:
                                        embed.title = "URLscan.io detected no threats"
                                        embed.color = 0x18bb9c
                                        embed.description = f"URLScan did not detect any threats associated with {url}"
                                        embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
                                        view.add_item(discord.ui.Button(label="View results", url=report_url, style=discord.ButtonStyle.link))
                                elif 'message' in res2 and res2['message'] == "Scan prevented":
                                    embed.title = "Domain is known safe"
                                    embed.description = f"The domain for {url} is whitelisted and safe from scanning."
                                    embed.color = 0x2d3e50
                                    view.add_item(discord.ui.Button(label="View results", url=report_url, style=discord.ButtonStyle.link))
                                else:
                                    embed.title = "Error occurred during URLScan"
                                    embed.description = f"Unable to determine the threat level for {url}."
                                    embed.color = 0xff4545

                                if 'verdicts' in res2 or ('message' in res2 and res2['message'] == "Scan prevented"):
                                    await ctx.send(embed=embed, view=view)
                                else:
                                    await ctx.send(embed=embed)
                except (json.JSONDecodeError, aiohttp.ClientError, asyncio.TimeoutError) as e:
                    await ctx.send(f"Error: {str(e)} for {url}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if not hasattr(self.bot, 'autoscan_enabled_guilds') or not self.bot.autoscan_enabled_guilds.get(message.guild.id, False):
            return

        if message.author.bot:
            return

        urls_to_scan = re.findall(r'(https?://\S+)', message.content)
        if not urls_to_scan:
            return

        ctx = await self.bot.get_context(message)
        log_channel_id = await self.config.guild(message.guild).log_channel()
        log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None

        for url in urls_to_scan:
            urlscan_key = await self.bot.get_shared_api_tokens("urlscan")
            api_key = urlscan_key.get("api_key")
            if api_key is None:
                continue

            headers = {
                "Content-Type": "application/json",
                "API-Key": api_key
            }
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "visibility": "public"}
                async with session.post('https://urlscan.io/api/v1/scan/', headers=headers, json=data, timeout=10) as r:
                    res = await r.json()
                    if 'result' not in res:
                        continue

                    report_api = res['api']
                    await asyncio.sleep(60)
                    async with session.get(report_api, timeout=10) as r2:
                        res2 = await r2.json()
                        if 'verdicts' in res2 and 'overall' in res2['verdicts'] and 'score' in res2['verdicts']['overall']:
                            threat_level = res2['verdicts']['overall']['score']
                            if threat_level != 0:
                                try:
                                    await message.delete()
                                    embed = discord.Embed(
                                        title="URLScan detected a threat",
                                        description=f"Deleted a suspicious URL posted by {message.author.mention}.",
                                        color=0xe25946
                                    )
                                    await message.channel.send(embed=embed)
                                    if log_channel:
                                        await log_channel.send(embed=embed)
                                except discord.NotFound:
                                    # Message was already deleted, possibly by another link filtering module
                                    pass
                                except discord.Forbidden:
                                    # Bot does not have permission to delete the message
                                    embed = discord.Embed(
                                        title="URLScan detected a threat",
                                        description=f"Detected a suspicious URL posted by {message.author.mention}, but I don't have permission to delete it.",
                                        color=0xe25946
                                    )
                                    await message.channel.send(embed=embed)
                                    if log_channel:
                                        await log_channel.send(embed=embed)
                                break
            
