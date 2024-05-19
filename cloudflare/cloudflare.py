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
    async def tools(self, ctx)
         """Different utility tools provided by Cloudflare."""
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid Cloudflare command passed.")

    @tools.command(name="whois")
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
            page = discord.Embed(title=f"WHOIS Information for {domain}", color=0xfffffe)
            field_count = 0

            def add_field_to_page(page, name, value):
                nonlocal field_count, pages
                page.add_field(name=name, value=value, inline=False)
                field_count += 1
                if field_count == 10:
                    pages.append(page)
                    page = discord.Embed(title=f"WHOIS Information for {domain}", color=0xfffffe)
                    field_count = 0
                return page

            if "administrative_city" in whois_info:
                administrative_city_value = f"**`{whois_info['administrative_city']}`**"
                page = add_field_to_page(page, "Administrative City", administrative_city_value)
            if "administrative_country" in whois_info:
                administrative_country_value = f"**`{whois_info['administrative_country']}`**"
                page = add_field_to_page(page, "Administrative Country", administrative_country_value)
            if "administrative_email" in whois_info:
                administrative_email_value = f"**`{whois_info['administrative_email']}`**"
                page = add_field_to_page(page, "Administrative Email", administrative_email_value)
            if "administrative_fax" in whois_info:
                administrative_fax_value = f"**`{whois_info['administrative_fax']}`**"
                page = add_field_to_page(page, "Administrative Fax", administrative_fax_value)
            if "administrative_fax_ext" in whois_info:
                administrative_fax_ext_value = f"**`{whois_info['administrative_fax_ext']}`**"
                page = add_field_to_page(page, "Administrative Fax Ext", administrative_fax_ext_value)
            if "administrative_id" in whois_info:
                administrative_id_value = f"**`{whois_info['administrative_id']}`**"
                page = add_field_to_page(page, "Administrative ID", administrative_id_value)
            if "administrative_name" in whois_info:
                administrative_name_value = f"**`{whois_info['administrative_name']}`**"
                page = add_field_to_page(page, "Administrative Name", administrative_name_value)
            if "administrative_org" in whois_info:
                administrative_org_value = f"**`{whois_info['administrative_org']}`**"
                page = add_field_to_page(page, "Administrative Org", administrative_org_value)
            if "administrative_phone" in whois_info:
                administrative_phone_value = f"**`{whois_info['administrative_phone']}`**"
                page = add_field_to_page(page, "Administrative Phone", administrative_phone_value)
            if "administrative_phone_ext" in whois_info:
                administrative_phone_ext_value = f"**`{whois_info['administrative_phone_ext']}`**"
                page = add_field_to_page(page, "Administrative Phone Ext", administrative_phone_ext_value)
            if "administrative_postal_code" in whois_info:
                administrative_postal_code_value = f"**`{whois_info['administrative_postal_code']}`**"
                page = add_field_to_page(page, "Administrative Postal Code", administrative_postal_code_value)
            if "administrative_province" in whois_info:
                administrative_province_value = f"**`{whois_info['administrative_province']}`**"
                page = add_field_to_page(page, "Administrative Province", administrative_province_value)
            if "administrative_street" in whois_info:
                administrative_street_value = f"**`{whois_info['administrative_street']}`**"
                page = add_field_to_page(page, "Administrative Street", administrative_street_value)
            if "billing_city" in whois_info:
                billing_city_value = f"**`{whois_info['billing_city']}`**"
                page = add_field_to_page(page, "Billing City", billing_city_value)
            if "billing_country" in whois_info:
                billing_country_value = f"**`{whois_info['billing_country']}`**"
                page = add_field_to_page(page, "Billing Country", billing_country_value)
            if "billing_email" in whois_info:
                billing_email_value = f"**`{whois_info['billing_email']}`**"
                page = add_field_to_page(page, "Billing Email", billing_email_value)
            if "billing_fax" in whois_info:
                billing_fax_value = f"**`{whois_info['billing_fax']}`**"
                page = add_field_to_page(page, "Billing Fax", billing_fax_value)
            if "billing_fax_ext" in whois_info:
                billing_fax_ext_value = f"**`{whois_info['billing_fax_ext']}`**"
                page = add_field_to_page(page, "Billing Fax Ext", billing_fax_ext_value)
            if "billing_id" in whois_info:
                billing_id_value = f"**`{whois_info['billing_id']}`**"
                page = add_field_to_page(page, "Billing ID", billing_id_value)
            if "billing_name" in whois_info:
                billing_name_value = f"**`{whois_info['billing_name']}`**"
                page = add_field_to_page(page, "Billing Name", billing_name_value)
            if "billing_org" in whois_info:
                billing_org_value = f"**`{whois_info['billing_org']}`**"
                page = add_field_to_page(page, "Billing Org", billing_org_value)
            if "billing_phone" in whois_info:
                billing_phone_value = f"**`{whois_info['billing_phone']}`**"
                page = add_field_to_page(page, "Billing Phone", billing_phone_value)
            if "billing_phone_ext" in whois_info:
                billing_phone_ext_value = f"**`{whois_info['billing_phone_ext']}`**"
                page = add_field_to_page(page, "Billing Phone Ext", billing_phone_ext_value)
            if "billing_postal_code" in whois_info:
                billing_postal_code_value = f"**`{whois_info['billing_postal_code']}`**"
                page = add_field_to_page(page, "Billing Postal Code", billing_postal_code_value)
            if "billing_province" in whois_info:
                billing_province_value = f"**`{whois_info['billing_province']}`**"
                page = add_field_to_page(page, "Billing Province", billing_province_value)
            if "billing_street" in whois_info:
                billing_street_value = f"**`{whois_info['billing_street']}`**"
                page = add_field_to_page(page, "Billing Street", billing_street_value)
            if "created_date" in whois_info:
                created_date = whois_info["created_date"]
                if isinstance(created_date, str):
                    from datetime import datetime
                    try:
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S")
                unix_timestamp = int(created_date.timestamp())
                discord_timestamp = f"**<t:{unix_timestamp}:F>**"
                page = add_field_to_page(page, "Created Date", discord_timestamp)
            if "dnssec" in whois_info:
                if "dnssec" in whois_info:
                    dnssec_value = whois_info["dnssec"]
                    dnssec_value = f"**`{dnssec_value}`**"
                    page = add_field_to_page(page, "DNSSEC", dnssec_value)
                if "domain" in whois_info:
                    domain_value = whois_info["domain"]
                    domain_value = f"**`{domain_value}`**"
                    page = add_field_to_page(page, "Domain", domain_value)
            if "expiration_date" in whois_info:
                expiration_date = whois_info["expiration_date"]
                if isinstance(expiration_date, str):
                    try:
                        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S")
                unix_timestamp = int(expiration_date.timestamp())
                discord_timestamp = f"**<t:{unix_timestamp}:F>**"
                page = add_field_to_page(page, "Expiration Date", discord_timestamp)
            if "extension" in whois_info:
                extension_value = whois_info["extension"]
                extension_value = f"**`{extension_value}`**"
                page = add_field_to_page(page, "Extension", extension_value)
            if "found" in whois_info:
                found_value = f"**`{whois_info['found']}`**"
                page = add_field_to_page(page, "Found", found_value)
            if "id" in whois_info:
                id_value = f"**`{whois_info['id']}`**"
                page = add_field_to_page(page, "ID", id_value)
            if "nameservers" in whois_info:
                nameservers_list = "\n".join(f"- **`{ns}`**" for ns in whois_info["nameservers"])
                page = add_field_to_page(page, "Nameservers", nameservers_list)
            if "punycode" in whois_info:
                punycode_value = f"**`{whois_info['punycode']}`**"
                page = add_field_to_page(page, "Punycode", punycode_value)
            if "registrant" in whois_info and whois_info["registrant"].strip():
                registrant_value = f"**`{whois_info['registrant']}`**"
                page = add_field_to_page(page, "Registrant", registrant_value)
            else:
                registrant_value = "**`REDACTED`**"
                page = add_field_to_page(page, "Registrant", registrant_value)
            if "registrant_city" in whois_info:
                registrant_city = f"**`{whois_info['registrant_city']}`**"
                page = add_field_to_page(page, "Registrant City", registrant_city)
            if "registrant_country" in whois_info:
                registrant_country = f"**`{whois_info['registrant_country']}`**"
                page = add_field_to_page(page, "Registrant Country", registrant_country)
            if "registrant_email" in whois_info:
                registrant_email = f"**`{whois_info['registrant_email']}`**"
                page = add_field_to_page(page, "Registrant Email", registrant_email)
            if "registrant_fax" in whois_info:
                registrant_fax = f"**`{whois_info['registrant_fax']}`**"
                page = add_field_to_page(page, "Registrant Fax", registrant_fax)
            if "registrant_fax_ext" in whois_info:
                registrant_fax_ext = f"**`{whois_info['registrant_fax_ext']}`**"
                page = add_field_to_page(page, "Registrant Fax Ext", registrant_fax_ext)
            if "registrant_id" in whois_info:
                registrant_id = f"**`{whois_info['registrant_id']}`**"
                page = add_field_to_page(page, "Registrant ID", registrant_id)
            if "registrant_name" in whois_info:
                registrant_name = f"**`{whois_info['registrant_name']}`**"
                page = add_field_to_page(page, "Registrant Name", registrant_name)
            if "registrant_org" in whois_info:
                registrant_org = f"**`{whois_info['registrant_org']}`**"
                page = add_field_to_page(page, "Registrant Org", registrant_org)
            if "registrant_phone" in whois_info:
                registrant_phone = f"**`{whois_info['registrant_phone']}`**"
                page = add_field_to_page(page, "Registrant Phone", registrant_phone)
            if "registrant_phone_ext" in whois_info:
                registrant_phone_ext = f"**`{whois_info['registrant_phone_ext']}`**"
                page = add_field_to_page(page, "Registrant Phone Ext", registrant_phone_ext)
            if "registrant_postal_code" in whois_info:
                registrant_postal_code = f"**`{whois_info['registrant_postal_code']}`**"
                page = add_field_to_page(page, "Registrant Postal Code", registrant_postal_code)
            if "registrant_province" in whois_info:
                registrant_province = f"**`{whois_info['registrant_province']}`**"
                page = add_field_to_page(page, "Registrant Province", registrant_province)
            if "registrant_street" in whois_info:
                registrant_street = f"**`{whois_info['registrant_street']}`**"
                page = add_field_to_page(page, "Registrant Street", registrant_street)
            if "registrar" in whois_info:
                registrar_value = f"**`{whois_info['registrar']}`**"
                page = add_field_to_page(page, "Registrar", registrar_value)
            if "registrar_city" in whois_info:
                registrar_city = f"**`{whois_info['registrar_city']}`**"
                page = add_field_to_page(page, "Registrar City", registrar_city)
            if "registrar_country" in whois_info:
                registrar_country = f"**`{whois_info['registrar_country']}`**"
                page = add_field_to_page(page, "Registrar Country", registrar_country)
            if "registrar_email" in whois_info:
                registrar_email = f"**`{whois_info['registrar_email']}`**"
                page = add_field_to_page(page, "Registrar Email", registrar_email)
            if "registrar_fax" in whois_info:
                registrar_fax = f"**`{whois_info['registrar_fax']}`**"
                page = add_field_to_page(page, "Registrar Fax", registrar_fax)
            if "registrar_fax_ext" in whois_info:
                registrar_fax_ext = f"**`{whois_info['registrar_fax_ext']}`**"
                page = add_field_to_page(page, "Registrar Fax Ext", registrar_fax_ext)
            if "registrar_id" in whois_info:
                registrar_id = f"**`{whois_info['registrar_id']}`**"
                page = add_field_to_page(page, "Registrar ID", registrar_id)
            if "registrar_name" in whois_info:
                registrar_name = f"**`{whois_info['registrar_name']}`**"
                page = add_field_to_page(page, "Registrar Name", registrar_name)
            if "registrar_org" in whois_info:
                registrar_org = f"**`{whois_info['registrar_org']}`**"
                page = add_field_to_page(page, "Registrar Org", registrar_org)
            if "registrar_phone" in whois_info:
                registrar_phone = f"**`{whois_info['registrar_phone']}`**"
                page = add_field_to_page(page, "Registrar Phone", registrar_phone)
            if "registrar_phone_ext" in whois_info:
                registrar_phone_ext = f"**`{whois_info['registrar_phone_ext']}`**"
                page = add_field_to_page(page, "Registrar Phone Ext", registrar_phone_ext)
            if "registrar_postal_code" in whois_info:
                registrar_postal_code = f"**`{whois_info['registrar_postal_code']}`**"
                page = add_field_to_page(page, "Registrar Postal Code", registrar_postal_code)
            if "registrar_province" in whois_info:
                registrar_province = f"**`{whois_info['registrar_province']}`**"
                page = add_field_to_page(page, "Registrar Province", registrar_province)
            if "registrar_street" in whois_info:
                registrar_street = f"**`{whois_info['registrar_street']}`**"
                page = add_field_to_page(page, "Registrar Street", registrar_street)
            if "status" in whois_info:
                status_value = f"**`{', '.join(whois_info['status'])}`**"
                page = add_field_to_page(page, "Status", status_value)
            if "technical_city" in whois_info:
                technical_city = f"**`{whois_info['technical_city']}`**"
                page = add_field_to_page(page, "Technical City", technical_city)
            if "technical_country" in whois_info:
                technical_country = f"**`{whois_info['technical_country']}`**"
                page = add_field_to_page(page, "Technical Country", technical_country)
            if "technical_email" in whois_info:
                technical_email = f"**`{whois_info['technical_email']}`**"
                page = add_field_to_page(page, "Technical Email", technical_email)
            if "technical_fax" in whois_info:
                technical_fax = f"**`{whois_info['technical_fax']}`**"
                page = add_field_to_page(page, "Technical Fax", technical_fax)
            if "technical_fax_ext" in whois_info:
                technical_fax_ext = f"**`{whois_info['technical_fax_ext']}`**"
                page = add_field_to_page(page, "Technical Fax Ext", technical_fax_ext)
            if "technical_id" in whois_info:
                technical_id = f"**`{whois_info['technical_id']}`**"
                page = add_field_to_page(page, "Technical ID", technical_id)
            if "technical_name" in whois_info:
                technical_name = f"**`{whois_info['technical_name']}`**"
                page = add_field_to_page(page, "Technical Name", technical_name)
            if "technical_org" in whois_info:
                technical_org = f"**`{whois_info['technical_org']}`**"
                page = add_field_to_page(page, "Technical Org", technical_org)
            if "technical_phone" in whois_info:
                technical_phone = f"**`{whois_info['technical_phone']}`**"
                page = add_field_to_page(page, "Technical Phone", technical_phone)
            if "technical_phone_ext" in whois_info:
                technical_phone_ext = f"**`{whois_info['technical_phone_ext']}`**"
                page = add_field_to_page(page, "Technical Phone Ext", technical_phone_ext)
            if "technical_postal_code" in whois_info:
                technical_postal_code = f"**`{whois_info['technical_postal_code']}`**"
                page = add_field_to_page(page, "Technical Postal Code", technical_postal_code)
            if "technical_province" in whois_info:
                technical_province = f"**`{whois_info['technical_province']}`**"
                page = add_field_to_page(page, "Technical Province", technical_province)
            if "technical_street" in whois_info:
                technical_street = f"**`{whois_info['technical_street']}`**"
                page = add_field_to_page(page, "Technical Street", technical_street)
            if "updated_date" in whois_info:
                try:
                    updated_date = int(datetime.strptime(whois_info["updated_date"], "%Y-%m-%dT%H:%M:%S").timestamp())
                    page = add_field_to_page(page, "Updated Date", f"**<t:{updated_date}:F>**")
                except ValueError:
                    pass  # Handle the case where the date format is incorrect
                except AttributeError:
                    pass  # Handle the case where the date is not a string
            if "whois_server" in whois_info:
                whois_server = f"**`{whois_info['whois_server']}`**"
                page = add_field_to_page(page, "WHOIS Server", whois_server)

            if page.fields:
                pages.append(page)

            # Create a view with a button
            view = discord.ui.View()
            if "administrative_referral_url" in whois_info:
                button = discord.ui.Button(label="Admin", url=whois_info["administrative_referral_url"])
                view.add_item(button)
            if "billing_referral_url" in whois_info:
                button = discord.ui.Button(label="Billing", url=whois_info["billing_referral_url"])
                view.add_item(button)
            if "registrant_referral_url" in whois_info:
                button = discord.ui.Button(label="Registrant", url=whois_info["registrant_referral_url"])
                view.add_item(button)
            if "registrar_referral_url" in whois_info:
                button = discord.ui.Button(label="Registrar", url=whois_info["registrar_referral_url"])
                view.add_item(button)
            if "technical_referral_url" in whois_info:
                button = discord.ui.Button(label="Technical", url=whois_info["technical_referral_url"])
                view.add_item(button)

            message = await ctx.send(embed=pages[0], view=view)

            current_page = 0
            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("❌")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

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

                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break
        
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
