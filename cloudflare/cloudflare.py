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
        
        # Safely retrieve API tokens with default values
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

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

            fields = [
                ("Administrative City", whois_info.get("administrative_city", "N/A")),
                ("Administrative Country", whois_info.get("administrative_country", "N/A")),
                ("Administrative Email", whois_info.get("administrative_email", "N/A")),
                ("Administrative Fax", whois_info.get("administrative_fax", "N/A")),
                ("Administrative Fax Ext", whois_info.get("administrative_fax_ext", "N/A")),
                ("Administrative ID", whois_info.get("administrative_id", "N/A")),
                ("Administrative Name", whois_info.get("administrative_name", "N/A")),
                ("Administrative Org", whois_info.get("administrative_org", "N/A")),
                ("Administrative Phone", whois_info.get("administrative_phone", "N/A")),
                ("Administrative Phone Ext", whois_info.get("administrative_phone_ext", "N/A")),
                ("Administrative Postal Code", whois_info.get("administrative_postal_code", "N/A")),
                ("Administrative Province", whois_info.get("administrative_province", "N/A")),
                ("Administrative Referral URL", whois_info.get("administrative_referral_url", "N/A")),
                ("Administrative Street", whois_info.get("administrative_street", "N/A")),
                ("Billing City", whois_info.get("billing_city", "N/A")),
                ("Billing Country", whois_info.get("billing_country", "N/A")),
                ("Billing Email", whois_info.get("billing_email", "N/A")),
                ("Billing Fax", whois_info.get("billing_fax", "N/A")),
                ("Billing Fax Ext", whois_info.get("billing_fax_ext", "N/A")),
                ("Billing ID", whois_info.get("billing_id", "N/A")),
                ("Billing Name", whois_info.get("billing_name", "N/A")),
                ("Billing Org", whois_info.get("billing_org", "N/A")),
                ("Billing Phone", whois_info.get("billing_phone", "N/A")),
                ("Billing Phone Ext", whois_info.get("billing_phone_ext", "N/A")),
                ("Billing Postal Code", whois_info.get("billing_postal_code", "N/A")),
                ("Billing Province", whois_info.get("billing_province", "N/A")),
                ("Billing Referral URL", whois_info.get("billing_referral_url", "N/A")),
                ("Billing Street", whois_info.get("billing_street", "N/A")),
                ("Created Date", whois_info.get("created_date", "N/A")),
                ("DNSSEC", whois_info.get("dnssec", "N/A")),
                ("Domain", whois_info.get("domain", "N/A")),
                ("Expiration Date", whois_info.get("expiration_date", "N/A")),
                ("Extension", whois_info.get("extension", "N/A")),
                ("Found", whois_info.get("found", "N/A")),
                ("ID", whois_info.get("id", "N/A")),
                ("Nameservers", ", ".join(whois_info.get("nameservers", []))),
                ("Punycode", whois_info.get("punycode", "N/A")),
                ("Registrant", whois_info.get("registrant", "N/A")),
                ("Registrant City", whois_info.get("registrant_city", "N/A")),
                ("Registrant Country", whois_info.get("registrant_country", "N/A")),
                ("Registrant Email", whois_info.get("registrant_email", "N/A")),
                ("Registrant Fax", whois_info.get("registrant_fax", "N/A")),
                ("Registrant Fax Ext", whois_info.get("registrant_fax_ext", "N/A")),
                ("Registrant ID", whois_info.get("registrant_id", "N/A")),
                ("Registrant Name", whois_info.get("registrant_name", "N/A")),
                ("Registrant Org", whois_info.get("registrant_org", "N/A")),
                ("Registrant Phone", whois_info.get("registrant_phone", "N/A")),
                ("Registrant Phone Ext", whois_info.get("registrant_phone_ext", "N/A")),
                ("Registrant Postal Code", whois_info.get("registrant_postal_code", "N/A")),
                ("Registrant Province", whois_info.get("registrant_province", "N/A")),
                ("Registrant Referral URL", whois_info.get("registrant_referral_url", "N/A")),
                ("Registrant Street", whois_info.get("registrant_street", "N/A")),
                ("Registrar", whois_info.get("registrar", "N/A")),
                ("Registrar City", whois_info.get("registrar_city", "N/A")),
                ("Registrar Country", whois_info.get("registrar_country", "N/A")),
                ("Registrar Email", whois_info.get("registrar_email", "N/A")),
                ("Registrar Fax", whois_info.get("registrar_fax", "N/A")),
                ("Registrar Fax Ext", whois_info.get("registrar_fax_ext", "N/A")),
                ("Registrar ID", whois_info.get("registrar_id", "N/A")),
                ("Registrar Name", whois_info.get("registrar_name", "N/A")),
                ("Registrar Org", whois_info.get("registrar_org", "N/A")),
                ("Registrar Phone", whois_info.get("registrar_phone", "N/A")),
                ("Registrar Phone Ext", whois_info.get("registrar_phone_ext", "N/A")),
                ("Registrar Postal Code", whois_info.get("registrar_postal_code", "N/A")),
                ("Registrar Province", whois_info.get("registrar_province", "N/A")),
                ("Registrar Referral URL", whois_info.get("registrar_referral_url", "N/A")),
                ("Registrar Street", whois_info.get("registrar_street", "N/A")),
                ("Status", ", ".join(whois_info.get("status", []))),
                ("Technical City", whois_info.get("technical_city", "N/A")),
                ("Technical Country", whois_info.get("technical_country", "N/A")),
                ("Technical Email", whois_info.get("technical_email", "N/A")),
                ("Technical Fax", whois_info.get("technical_fax", "N/A")),
                ("Technical Fax Ext", whois_info.get("technical_fax_ext", "N/A")),
                ("Technical ID", whois_info.get("technical_id", "N/A")),
                ("Technical Name", whois_info.get("technical_name", "N/A")),
                ("Technical Org", whois_info.get("technical_org", "N/A")),
                ("Technical Phone", whois_info.get("technical_phone", "N/A")),
                ("Technical Phone Ext", whois_info.get("technical_phone_ext", "N/A")),
                ("Technical Postal Code", whois_info.get("technical_postal_code", "N/A")),
                ("Technical Province", whois_info.get("technical_province", "N/A")),
                ("Technical Referral URL", whois_info.get("technical_referral_url", "N/A")),
                ("Technical Street", whois_info.get("technical_street", "N/A")),
                ("Updated Date", whois_info.get("updated_date", "N/A")),
                ("WHOIS Server", whois_info.get("whois_server", "N/A"))
            ]

            pages = []
            page = discord.Embed(title=f"WHOIS Information for {domain}", color=discord.Color.blue())
            for name, value in fields:
                if value != "N/A":
                    if len(page.fields) == 15:
                        pages.append(page)
                        page = discord.Embed(title=f"WHOIS Information for {domain}", color=discord.Color.blue())
                    page.add_field(name=name, value=value, inline=False)
            if page.fields:
                pages.append(page)

            message = await ctx.send(embed=pages[0])

            current_page = 0
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
                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)

                    except asyncio.TimeoutError:
                        break




    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
