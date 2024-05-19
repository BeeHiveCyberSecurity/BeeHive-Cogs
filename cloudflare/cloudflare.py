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

            pages = []
            page = discord.Embed(title=f"WHOIS Information for {domain}", color=discord.Color.blue())

            if "administrative_city" in whois_info:
                page.add_field(name="Administrative City", value=whois_info["administrative_city"], inline=False)
            if "administrative_country" in whois_info:
                page.add_field(name="Administrative Country", value=whois_info["administrative_country"], inline=False)
            if "administrative_email" in whois_info:
                page.add_field(name="Administrative Email", value=whois_info["administrative_email"], inline=False)
            if "administrative_fax" in whois_info:
                page.add_field(name="Administrative Fax", value=whois_info["administrative_fax"], inline=False)
            if "administrative_fax_ext" in whois_info:
                page.add_field(name="Administrative Fax Ext", value=whois_info["administrative_fax_ext"], inline=False)
            if "administrative_id" in whois_info:
                page.add_field(name="Administrative ID", value=whois_info["administrative_id"], inline=False)
            if "administrative_name" in whois_info:
                page.add_field(name="Administrative Name", value=whois_info["administrative_name"], inline=False)
            if "administrative_org" in whois_info:
                page.add_field(name="Administrative Org", value=whois_info["administrative_org"], inline=False)
            if "administrative_phone" in whois_info:
                page.add_field(name="Administrative Phone", value=whois_info["administrative_phone"], inline=False)
            if "administrative_phone_ext" in whois_info:
                page.add_field(name="Administrative Phone Ext", value=whois_info["administrative_phone_ext"], inline=False)
            if "administrative_postal_code" in whois_info:
                page.add_field(name="Administrative Postal Code", value=whois_info["administrative_postal_code"], inline=False)
            if "administrative_province" in whois_info:
                page.add_field(name="Administrative Province", value=whois_info["administrative_province"], inline=False)
            if "administrative_street" in whois_info:
                page.add_field(name="Administrative Street", value=whois_info["administrative_street"], inline=False)
            if "billing_city" in whois_info:
                page.add_field(name="Billing City", value=whois_info["billing_city"], inline=False)
            if "billing_country" in whois_info:
                page.add_field(name="Billing Country", value=whois_info["billing_country"], inline=False)
            if "billing_email" in whois_info:
                page.add_field(name="Billing Email", value=whois_info["billing_email"], inline=False)
            if "billing_fax" in whois_info:
                page.add_field(name="Billing Fax", value=whois_info["billing_fax"], inline=False)
            if "billing_fax_ext" in whois_info:
                page.add_field(name="Billing Fax Ext", value=whois_info["billing_fax_ext"], inline=False)
            if "billing_id" in whois_info:
                page.add_field(name="Billing ID", value=whois_info["billing_id"], inline=False)
            if "billing_name" in whois_info:
                page.add_field(name="Billing Name", value=whois_info["billing_name"], inline=False)
            if "billing_org" in whois_info:
                page.add_field(name="Billing Org", value=whois_info["billing_org"], inline=False)
            if "billing_phone" in whois_info:
                page.add_field(name="Billing Phone", value=whois_info["billing_phone"], inline=False)
            if "billing_phone_ext" in whois_info:
                page.add_field(name="Billing Phone Ext", value=whois_info["billing_phone_ext"], inline=False)
            if "billing_postal_code" in whois_info:
                page.add_field(name="Billing Postal Code", value=whois_info["billing_postal_code"], inline=False)
            if "billing_province" in whois_info:
                page.add_field(name="Billing Province", value=whois_info["billing_province"], inline=False)
            if "billing_street" in whois_info:
                page.add_field(name="Billing Street", value=whois_info["billing_street"], inline=False)
            if "created_date" in whois_info:
                created_date = whois_info["created_date"]
                if isinstance(created_date, str):
                    from datetime import datetime
                    try:
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S")
                unix_timestamp = int(created_date.timestamp())
                discord_timestamp = f"<t:{unix_timestamp}:F>"
                page.add_field(name="Created Date", value=discord_timestamp, inline=False)
            if "dnssec" in whois_info:
                page.add_field(name="DNSSEC", value=whois_info["dnssec"], inline=False)
            if "domain" in whois_info:
                page.add_field(name="Domain", value=whois_info["domain"], inline=False)
            if "expiration_date" in whois_info:
                expiration_date = whois_info["expiration_date"]
                if isinstance(expiration_date, str):
                    try:
                        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S")
                unix_timestamp = int(expiration_date.timestamp())
                discord_timestamp = f"<t:{unix_timestamp}:F>"
                page.add_field(name="Expiration Date", value=discord_timestamp, inline=False)
            if "extension" in whois_info:
                page.add_field(name="Extension", value=whois_info["extension"], inline=False)
            if "found" in whois_info:
                page.add_field(name="Found", value=whois_info["found"], inline=False)
            if "id" in whois_info:
                page.add_field(name="ID", value=whois_info["id"], inline=False)
            if "nameservers" in whois_info:
                page.add_field(name="Nameservers", value=", ".join(whois_info["nameservers"]), inline=False)
            if "punycode" in whois_info:
                page.add_field(name="Punycode", value=whois_info["punycode"], inline=False)
            if "registrant" in whois_info:
                page.add_field(name="Registrant", value=whois_info["registrant"], inline=False)
            if "registrant_city" in whois_info:
                page.add_field(name="Registrant City", value=whois_info["registrant_city"], inline=False)
            if "registrant_country" in whois_info:
                page.add_field(name="Registrant Country", value=whois_info["registrant_country"], inline=False)
            if "registrant_email" in whois_info:
                page.add_field(name="Registrant Email", value=whois_info["registrant_email"], inline=False)
            if "registrant_fax" in whois_info:
                page.add_field(name="Registrant Fax", value=whois_info["registrant_fax"], inline=False)
            if "registrant_fax_ext" in whois_info:
                page.add_field(name="Registrant Fax Ext", value=whois_info["registrant_fax_ext"], inline=False)
            if "registrant_id" in whois_info:
                page.add_field(name="Registrant ID", value=whois_info["registrant_id"], inline=False)
            if "registrant_name" in whois_info:
                page.add_field(name="Registrant Name", value=whois_info["registrant_name"], inline=False)
            if "registrant_org" in whois_info:
                page.add_field(name="Registrant Org", value=whois_info["registrant_org"], inline=False)
            if "registrant_phone" in whois_info:
                page.add_field(name="Registrant Phone", value=whois_info["registrant_phone"], inline=False)
            if "registrant_phone_ext" in whois_info:
                page.add_field(name="Registrant Phone Ext", value=whois_info["registrant_phone_ext"], inline=False)
            if "registrant_postal_code" in whois_info:
                page.add_field(name="Registrant Postal Code", value=whois_info["registrant_postal_code"], inline=False)
            if "registrant_province" in whois_info:
                page.add_field(name="Registrant Province", value=whois_info["registrant_province"], inline=False)
            if "registrant_street" in whois_info:
                page.add_field(name="Registrant Street", value=whois_info["registrant_street"], inline=False)
            if "registrar" in whois_info:
                page.add_field(name="Registrar", value=whois_info["registrar"], inline=False)
            if "registrar_city" in whois_info:
                page.add_field(name="Registrar City", value=whois_info["registrar_city"], inline=False)
            if "registrar_country" in whois_info:
                page.add_field(name="Registrar Country", value=whois_info["registrar_country"], inline=False)
            if "registrar_email" in whois_info:
                page.add_field(name="Registrar Email", value=whois_info["registrar_email"], inline=False)
            if "registrar_fax" in whois_info:
                page.add_field(name="Registrar Fax", value=whois_info["registrar_fax"], inline=False)
            if "registrar_fax_ext" in whois_info:
                page.add_field(name="Registrar Fax Ext", value=whois_info["registrar_fax_ext"], inline=False)
            if "registrar_id" in whois_info:
                page.add_field(name="Registrar ID", value=whois_info["registrar_id"], inline=False)
            if "registrar_name" in whois_info:
                page.add_field(name="Registrar Name", value=whois_info["registrar_name"], inline=False)
            if "registrar_org" in whois_info:
                page.add_field(name="Registrar Org", value=whois_info["registrar_org"], inline=False)
            if "registrar_phone" in whois_info:
                page.add_field(name="Registrar Phone", value=whois_info["registrar_phone"], inline=False)
            if "registrar_phone_ext" in whois_info:
                page.add_field(name="Registrar Phone Ext", value=whois_info["registrar_phone_ext"], inline=False)
            if "registrar_postal_code" in whois_info:
                page.add_field(name="Registrar Postal Code", value=whois_info["registrar_postal_code"], inline=False)
            if "registrar_province" in whois_info:
                page.add_field(name="Registrar Province", value=whois_info["registrar_province"], inline=False)
            if "registrar_street" in whois_info:
                page.add_field(name="Registrar Street", value=whois_info["registrar_street"], inline=False)
            if "status" in whois_info:
                page.add_field(name="Status", value=", ".join(whois_info["status"]), inline=False)
            if "technical_city" in whois_info:
                page.add_field(name="Technical City", value=whois_info["technical_city"], inline=False)
            if "technical_country" in whois_info:
                page.add_field(name="Technical Country", value=whois_info["technical_country"], inline=False)
            if "technical_email" in whois_info:
                page.add_field(name="Technical Email", value=whois_info["technical_email"], inline=False)
            if "technical_fax" in whois_info:
                page.add_field(name="Technical Fax", value=whois_info["technical_fax"], inline=False)
            if "technical_fax_ext" in whois_info:
                page.add_field(name="Technical Fax Ext", value=whois_info["technical_fax_ext"], inline=False)
            if "technical_id" in whois_info:
                page.add_field(name="Technical ID", value=whois_info["technical_id"], inline=False)
            if "technical_name" in whois_info:
                page.add_field(name="Technical Name", value=whois_info["technical_name"], inline=False)
            if "technical_org" in whois_info:
                page.add_field(name="Technical Org", value=whois_info["technical_org"], inline=False)
            if "technical_phone" in whois_info:
                page.add_field(name="Technical Phone", value=whois_info["technical_phone"], inline=False)
            if "technical_phone_ext" in whois_info:
                page.add_field(name="Technical Phone Ext", value=whois_info["technical_phone_ext"], inline=False)
            if "technical_postal_code" in whois_info:
                page.add_field(name="Technical Postal Code", value=whois_info["technical_postal_code"], inline=False)
            if "technical_province" in whois_info:
                page.add_field(name="Technical Province", value=whois_info["technical_province"], inline=False)
            if "technical_street" in whois_info:
                page.add_field(name="Technical Street", value=whois_info["technical_street"], inline=False)
            if "updated_date" in whois_info:
                page.add_field(name="Updated Date", value=whois_info["updated_date"], inline=False)
            if "whois_server" in whois_info:
                page.add_field(name="WHOIS Server", value=whois_info["whois_server"], inline=False)

            if page.fields:
                pages.append(page)

            # Create a view with a button
            view = discord.ui.View()
            if "administrative_referral_url" in whois_info:
                button = discord.ui.Button(label="Administrative Referral URL", url=whois_info["administrative_referral_url"])
                view.add_item(button)
            if "billing_referral_url" in whois_info:
                button = discord.ui.Button(label="Billing contact", url=whois_info["billing_referral_url"])
                view.add_item(button)
            if "registrant_referral_url" in whois_info:
                button = discord.ui.Button(label="Registrant contact", url=whois_info["registrant_referral_url"])
                view.add_item(button)
            if "registrar_referral_url" in whois_info:
                button = discord.ui.Button(label="Registrar contact", url=whois_info["registrar_referral_url"])
                view.add_item(button)
            if "technical_referral_url" in whois_info:
                button = discord.ui.Button(label="Technical contact", url=whois_info["technical_referral_url"])
                view.add_item(button)

            message = await ctx.send(embed=pages[0], view=view)

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
