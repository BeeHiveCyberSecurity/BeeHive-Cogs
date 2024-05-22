import aiohttp #type: ignore
import asyncio
import discord #type: ignore
import json
import re
from redbot.core import commands #type: ignore 
from redbot.core import app_commands #type: ignore
from redbot.core import Config #type: ignore

class URLScan(commands.Cog):
    """URLScan file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "autoscan_enabled": False
        }
        self.config.register_guild(**default_guild)

    @commands.group(name='urlscan', help="Scan URL's for dangerous content", invoke_without_command=True)
    async def urlscan(self, ctx, *, urls: str = None):
        """Scan a URL using urlscan.io"""
        await self.scan_urls(ctx, urls)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @urlscan.command(name="autoscan", description="Toggle automatic URL scanning in messages")
    async def autoscan(self, ctx, state: bool = None):
        """Toggle automatic URL scanning in messages"""
        if state is None:
            state = await self.config.guild(ctx.guild).autoscan_enabled()
            if state:
                embed = discord.Embed(title="URLScan Status", description="Automatic URL scanning is currently enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="URLScan Status", description="Automatic URL scanning is currently disabled.", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            await self.config.guild(ctx.guild).autoscan_enabled.set(state)
            if state:
                embed = discord.Embed(title="URLScan Status", description="Automatic URL scanning has been enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="URLScan Status", description="Automatic URL scanning has been disabled.", color=0xff4545)
                await ctx.send(embed=embed)

    async def scan_urls(self, ctx, urls: str = None):
        urlscan_key = await self.bot.get_shared_api_tokens("urlscan")
        if urlscan_key.get("api_key") is None:
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
            "API-Key": urlscan_key["api_key"]
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

                                embed = discord.Embed(url=report_url)
                                if 'verdicts' in res2 and 'overall' in res2['verdicts'] and 'score' in res2['verdicts']['overall']:
                                    threat_level = res2['verdicts']['overall']['score']
                                    if threat_level != 0:
                                        embed.title = "URL is suspicious"
                                        embed.description = f"URLScan says {url} is suspicious!\n\nFor your own safety, please don't click it."
                                        embed.color = 0xFF4545
                                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning-outline.png")
                                        view.add_item(discord.ui.Button(label="View results", url=report_url, style=discord.ButtonStyle.link))
                                    else:
                                        embed.title = "URL is safe"
                                        embed.color = 0x2BBD8E
                                        embed.description = f"URLScan did not detect any threats associated with {url}"
                                        embed.add_field(name="Overall verdict", value="Scanned and found safe", inline=False)
                                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                                        view.add_item(discord.ui.Button(label="View results", url=report_url, style=discord.ButtonStyle.link))
                                elif 'message' in res2 and res2['message'] == "Scan prevented":
                                    embed.title = "Domain is whitelisted"
                                    embed.description = f"The domain for {url} is whitelisted and safe from scanning."
                                    embed.color = 0x2BBD8E
                                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle-outline.png")
                                    view.add_item(discord.ui.Button(label="View results", url=report_url, style=discord.ButtonStyle.link))
                                else:
                                    embed.title = "Error occurred during URLScan"
                                    embed.description = f"Unable to determine the threat level for {url}."
                                    embed.color = 0xFFD700
                                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/warning-outline.png")

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
        for url in urls_to_scan:
            urlscan_key = await self.bot.get_shared_api_tokens("urlscan")
            headers = {
                "Content-Type": "application/json",
                "API-Key": urlscan_key["api_key"]
            }
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "visibility": "public"}
                async with session.post('https://urlscan.io/api/v1/scan/', headers=headers, json=data, timeout=10) as r:
                    res = await r.json()
                    if 'result' not in res:
                        continue

                    report_api = res['api']
                    await asyncio.sleep(30)
                    async with session.get(report_api, timeout=10) as r2:
                        res2 = await r2.json()
                        if 'verdicts' in res2 and 'overall' in res2['verdicts'] and 'score' in res2['verdicts']['overall']:
                            threat_level = res2['verdicts']['overall']['score']
                            if threat_level != 0:
                                try:
                                    await message.delete()
                                    embed = discord.Embed(
                                        title="Threat detected by URLScan",
                                        description=f"Deleted a suspicious URL posted by {message.author.mention}.",
                                        color=0xFF4545
                                    )
                                    await message.channel.send(embed=embed)
                                except discord.NotFound:
                                    # Message was already deleted, possibly by another link filtering module
                                    pass
                                except discord.Forbidden:
                                    # Bot does not have permission to delete the message
                                    embed = discord.Embed(
                                        title="Threat detected by URLScan",
                                        description=f"Detected a suspicious URL posted by {message.author.mention}, but I don't have permission to delete it.",
                                        color=0xFF4545
                                    )
                                    await message.channel.send(embed=embed)
                                break
            
