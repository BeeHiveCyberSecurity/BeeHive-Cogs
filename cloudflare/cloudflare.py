import discord
import asyncio
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
        }
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession()

    @commands.group()
    async def cloudflare(self, ctx):
        """Cloudflare command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Cloudflare command passed.")

    @commands.is_owner()
    @cloudflare.command()
    async def setapikey(self, ctx, api_key: str):
        """Set the Cloudflare API key."""
        await self.config.api_key.set(api_key)
        await ctx.send("Cloudflare API key set.")

    @commands.is_owner()
    @cloudflare.command()
    async def setemail(self, ctx, email: str):
        """Set the Cloudflare account email."""
        await self.config.email.set(email)
        await ctx.send("Cloudflare email set.")

    @commands.is_owner()
    @cloudflare.command()
    async def setbearer(self, ctx, bearer_token: str):
        """Set the Cloudflare Bearer token."""
        await self.config.api_key.set(bearer_token)
        await ctx.send("Cloudflare Bearer token set.")

    @commands.is_owner()
    @cloudflare.command()
    async def getzones(self, ctx):
        """Get the list of zones from Cloudflare."""
        api_key = await self.config.api_key()
        email = await self.config.email()
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
            embed = discord.Embed(title="Cloudflare Zones", description="\n".join(pages[current_page]), color=discord.Color.blue())
            message = await ctx.send(embed=embed)

            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

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

                    except asyncio.TimeoutError:
                        break

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
