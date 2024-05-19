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
            "account_id": None,
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
        obfuscated_api_key = api_key[:4] + "****" + api_key[-4:]
        await ctx.send(f"Cloudflare API key set: **`{obfuscated_api_key}`**")

    @commands.is_owner()
    @cloudflare.command()
    async def setemail(self, ctx, email: str):
        """Set the Cloudflare account email."""
        await self.config.email.set(email)
        obfuscated_email = email[:2] + "****" + email.split("@")[-1]
        await ctx.send(f"Cloudflare email set: **`{obfuscated_email}`**")

    @commands.is_owner()
    @cloudflare.command()
    async def setbearer(self, ctx, bearer_token: str):
        """Set the Cloudflare Bearer token."""
        await self.config.api_key.set(bearer_token)
        obfuscated_bearer_token = bearer_token[:4] + "****" + bearer_token[-4:]
        await ctx.send(f"Cloudflare Bearer token set: **`{obfuscated_bearer_token}`**")

    @commands.is_owner()
    @cloudflare.command()
    async def setaccountid(self, ctx, account_id: str):
        """Set the Cloudflare Account ID."""
        await self.config.account_id.set(account_id)
        obfuscated_account_id = account_id[:4] + "****" + account_id[-4:]
        await ctx.send(f"Cloudflare Account ID set: **`{obfuscated_account_id}`**")
        
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

    @cloudflare.command(name="whois")
    async def whois(self, ctx, domain: str):
        """
        Query WHOIS information for a given domain.
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens["email"]
        api_key = api_tokens["api_key"]
        bearer_token = api_tokens["bearer_token"]
        account_id = api_tokens["account_id"]

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        async with self.session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/whois?domain={domain}", headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch WHOIS information: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch WHOIS information.")
                return

            whois_info = data.get("result", {})

            embed = discord.Embed(title=f"WHOIS Information for {domain}", color=discord.Color.blue())
            for key, value in whois_info.items():
                embed.add_field(name=key, value=value, inline=False)

            await ctx.send(embed=embed)




    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
