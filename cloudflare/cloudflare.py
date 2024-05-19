import discord
import asyncio
import time
from datetime import datetime
from redbot.core import commands, Config
import aiohttp

class Cloudflare(commands.Cog):
    """A Red-Discordbot cog to interact with the Cloudflare API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "api_key": None,
            "email": None,
            "bearer_token": None,
            "account_id": None,
        }
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession()

    @commands.group()
    async def tools(self, ctx):
         """Different utility tools provided by Cloudflare."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Cloudflare command passed.")
  
    @commands.group()
    async def cloudflare(self, ctx):
        """Cloudflare command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Cloudflare command passed.")
        
    @commands.is_owner()
    @cloudflare.command()
    async def getzones(self, ctx):
        """Get the list of zones from Cloudflare."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        if not api_key or not email:
            await ctx.send("API key or email not set.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get("https://api.cloudflare.com/client/v4/zones", headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch zones: {response.status}")
                return

            data = await response.json()
            zones = data.get("result", [])
            if not zones:
                await ctx.send("No zones found.")
                return

            zone_names = [zone["name"] for zone in zones]
            pages = [zone_names[i:i + 10] for i in range(0, len(zone_names), 10)]

            current_page = 0
            embed = discord.Embed(title="Zones in Cloudflare account", description="\n".join(pages[current_page]), color=discord.Color.orange())
            message = await ctx.send(embed=embed)

            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("❌")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

                        if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                            current_page += 1
                            embed.description = "\n".join(pages[current_page])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            embed.description = "\n".join(pages[current_page])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                    except asyncio.TimeoutError:
                        break

                # Remove reactions after timeout
                try:
                    await message.clear_reactions()
                except discord.Forbidden:
                    pass

    




    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
