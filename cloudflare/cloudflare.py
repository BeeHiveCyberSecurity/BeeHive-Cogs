import discord #type: ignore
import asyncio
import time
from datetime import datetime
from redbot.core import commands, Config #type: ignore
import aiohttp #type: ignore
import ipaddress
import json
import io

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
    
    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def keystore(self, ctx):
        """Fetch keys in use for development purposes only"""

    @commands.is_owner()
    @keystore.command(name="email")
    async def email(self, ctx):
        """Fetch the current Cloudflare email"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        if not email:
            embed = discord.Embed(title="Error", description="Email not set.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare email**\n\n```{email}```")
            embed = discord.Embed(title="Success", description="The Cloudflare email has been sent to your DMs.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="apikey")
    async def api_key(self, ctx):
        """Fetch the current Cloudflare API key"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        if not api_key:
            embed = discord.Embed(title="Error", description="API key not set.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare API key**\n\n```{api_key}```")
            embed = discord.Embed(title="Success", description="The Cloudflare API key has been sent to your DMs.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="bearertoken")
    async def bearer_token(self, ctx):
        """Fetch the current Cloudflare bearer token"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        if not bearer_token:
            embed = discord.Embed(title="Error", description="Bearer token not set.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare bearer token**\n\n```{bearer_token}```")
            embed = discord.Embed(title="Success", description="The Cloudflare bearer token has been sent to your DMs.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="accountid")
    async def account_id(self, ctx):
        """Fetch the current Cloudflare account ID"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        if not account_id:
            embed = discord.Embed(title="Error", description="Account ID not set.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare Account ID**\n\n```{account_id}```")
            embed = discord.Embed(title="Success", description="The Cloudflare Account ID has been sent to your DMs.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="zoneid")
    async def zone_id(self, ctx):
        """Fetch the current Cloudflare zone ID"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        zone_id = api_tokens.get("zone_id")
        if not zone_id:
            embed = discord.Embed(title="Error", description="Zone ID not set.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare Zone ID**\n\n```{zone_id}```")
            embed = discord.Embed(title="Success", description="The Cloudflare Zone ID has been sent to your DMs.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.group()
    async def botmanagement(self, ctx):
        "Cloudflare bot  management subtext"

    @commands.is_owner()
    @botmanagement.command(name="get")
    async def get_bot_management_config(self, ctx):
        """Get the current bot management config from Cloudflare."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        zone_id = api_tokens.get("zone_id")
        
        if not api_key or not email or not zone_id:
            await ctx.send("API key, email, or zone ID not set.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/bot_management"
        
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch bot management config: {response.status}")
                return

            data = await response.json()
            bot_management_config = data.get("result", {})
            if not bot_management_config:
                await ctx.send("No bot management config found.")
                return

            embed = discord.Embed(
                title="Bot Management Config",
                description="Current bot management configuration from Cloudflare",
                color=discord.Color.blue()
            )

            def format_value(value):
                return value.upper() if isinstance(value, str) else str(value).upper()

            embed.add_field(name="Enable JS", value=f"**`{format_value(bot_management_config.get('enable_js', 'Not set'))}`**", inline=False)
            embed.add_field(name="Optimize Wordpress", value=f"**`{format_value(bot_management_config.get('optimize_wordpress', 'Not set'))}`**", inline=False)
            embed.add_field(name="Suppress Session Score", value=f"**`{format_value(bot_management_config.get('suppress_session_score', 'Not set'))}`**", inline=False)
            embed.add_field(name="Super Bot Fight Mode", value="", inline=False)
            embed.add_field(name="Definitely automated", value=f"**`{format_value(bot_management_config.get('sbfm_definitely_automated', 'Not set'))}`**", inline=True)
            embed.add_field(name="Verified bots", value=f"**`{format_value(bot_management_config.get('sbfm_verified_bots', 'Not set'))}`**", inline=True)
            embed.add_field(name="Static resource protection", value=f"**`{format_value(bot_management_config.get('sbfm_static_resource_protection', 'Not set'))}`**", inline=True)
            embed.add_field(name="Using latest model", value=f"**`{format_value(bot_management_config.get('using_latest_model', 'Not set'))}`**", inline=False)

            await ctx.send(embed=embed)
    @commands.group()
    async def zones(self, ctx):
        """Cloudflare command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Cloudflare command passed.")
        
    @commands.is_owner()
    @zones.command(name="get")
    async def get(self, ctx):
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

    @commands.group(invoke_without_command=False)
    async def intel(self, ctx):
        """Cloudforce One packages the vital aspects of modern threat intelligence and operations to make organizations smarter, more responsive, and more secure. Learn more at https://www.cloudflare.com/application-services/products/cloudforceone/"""

    @intel.command(name="whois")
    async def whois(self, ctx, domain: str):
        """
        Query WHOIS information for a given domain.
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        async with self.session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/whois?domain={domain}", headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch WHOIS information: {response.status}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch WHOIS information.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
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

            for page in pages:
                page.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
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

    @intel.command(name="domain")
    async def querydomain(self, ctx, domain: str):
        """Query Cloudflare API for domain intelligence."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/domain"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {
            "domain": domain
        }

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    embed = discord.Embed(title=f"Domain intelligence for {result.get('domain', 'N/A')}", color=0xfffffe)
                    
                    if "domain" in result:
                        embed.add_field(name="Domain", value=f"**`{result['domain']}`**", inline=False)
                    if "risk_score" in result:
                        embed.add_field(name="Risk Score", value=f"**`{result['risk_score']}`**", inline=False)
                    if "popularity_rank" in result:
                        embed.add_field(name="Popularity Rank", value=f"**`{result['popularity_rank']}`**", inline=False)
                    if "application" in result and "name" in result["application"]:
                        embed.add_field(name="Application", value=f"**`{result['application']['name']}`**", inline=False)
                    if "additional_information" in result and "suspected_malware_family" in result["additional_information"]:
                        embed.add_field(name="Suspected Malware Family", value=f"`{result['additional_information']['suspected_malware_family']}`", inline=False)
                    if "content_categories" in result:
                        embed.add_field(name="Content Categories", value=", ".join([f"**`{cat['name']}`**" for cat in result["content_categories"]]), inline=False)
                    if "resolves_to_refs" in result:
                        embed.add_field(name="Resolves To", value=", ".join([f"**`{ref['value']}`**" for ref in result["resolves_to_refs"]]), inline=False)
                    if "inherited_content_categories" in result:
                        embed.add_field(name="Inherited Content Categories", value=", ".join([f"**`{cat['name']}`**" for cat in result["inherited_content_categories"]]), inline=False)
                    if "inherited_from" in result:
                        embed.add_field(name="Inherited From", value=f"**`{result['inherited_from']}`**", inline=False)
                    if "inherited_risk_types" in result:
                        embed.add_field(name="Inherited Risk Types", value=", ".join([f"**`{risk}`**" for risk in result["inherited_risk_types"]]), inline=False)
                    if "risk_types" in result:
                        embed.add_field(name="Risk Types", value=", ".join([f"**`{risk}`**" for risk in result["risk_types"]]), inline=False)

                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
                    await ctx.send(embed=embed)
                else:
                    error_embed = discord.Embed(title="Error", description=f"Error: {data['errors']}", color=0xff0000)
                    await ctx.send(embed=error_embed)
            else:
                error_embed = discord.Embed(title="Failed to query Cloudflare API", description=f"Status code: {response.status}", color=0xff0000)
                await ctx.send(embed=error_embed)

    @intel.command(name="ip")
    async def queryip(self, ctx, ip: str):
        """Query Cloudflare API for IP intelligence."""

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/ip"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {}
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.version == 4:
                params["ipv4"] = ip
            elif ip_obj.version == 6:
                params["ipv6"] = ip
        except ValueError:
            embed = discord.Embed(title="Error", description="Invalid IP address format.", color=0xff0000)
            await ctx.send(embed=embed)
            return

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"][0]
                    embed = discord.Embed(title=f"IP intelligence for {result['ip']}", color=0xfffffe)
                    
                    if "ip" in result:
                        embed.add_field(name="IP", value=f"**`{result['ip']}`**", inline=False)
                    if "belongs_to_ref" in result:
                        belongs_to = result["belongs_to_ref"]
                        if "description" in belongs_to:
                            embed.add_field(name="Belongs To", value=f"**`{belongs_to['description']}`**", inline=False)
                        if "country" in belongs_to:
                            embed.add_field(name="Country", value=f"**`{belongs_to['country']}`**", inline=False)
                        if "type" in belongs_to:
                            embed.add_field(name="Type", value=f"**`{belongs_to['type'].upper()}`**", inline=False)
                    if "ptr_lookup" in result and "ptr_domains" in result["ptr_lookup"]:
                        ptr_domains = ", ".join([f"**`{domain}`**" for domain in result["ptr_lookup"]["ptr_domains"]])
                        embed.add_field(name="PTR Domains", value=ptr_domains, inline=False)
                    if "risk_types" in result:
                        risk_types = ", ".join([f"**`{risk['name']}`**" for risk in result["risk_types"]])
                        embed.add_field(name="Risk Types", value=risk_types, inline=False)
                    if "result_info" in data:
                        result_info = data["result_info"]
                        embed.add_field(name="Total Count", value=f"**`{result_info['total_count']}`**", inline=False)
                        embed.add_field(name="Page", value=f"**`{result_info['page']}`**", inline=False)
                        embed.add_field(name="Per Page", value=f"**`{result_info['per_page']}`**", inline=False)
                        
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Error", description=f"Error: {data['errors']}", color=0xff0000)
                    await ctx.send(embed=embed)
            elif response.status == 400:
                embed = discord.Embed(title="Bad Request", description="The server could not understand the request due to invalid syntax.", color=0xff0000)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Failed to query Cloudflare API", description=f"Status code: {response.status}", color=0xff0000)
                await ctx.send(embed=embed)

    @intel.command(name="domainhistory")
    async def domainhistory(self, ctx, domain: str):
        """
        Fetch and display domain history from Cloudflare.
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/domain-history"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {"domain": domain}

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"][0]
                    embed = discord.Embed(title=f"Domain history for {domain}", color=0xfffffe)
                    
                    if "domain" in result:
                        embed.add_field(name="Domain", value=f"**`{result['domain']}`**", inline=False)
                    if "categorizations" in result:
                        categorizations = result["categorizations"]
                        for categorization in categorizations:
                            categories = ", ".join([f"**`{category['name']}`**" for category in categorization["categories"]])
                            embed.add_field(name="Categories", value=categories, inline=True)
                            start_timestamp = discord.utils.format_dt(discord.utils.parse_time(categorization['start']), style='R')
                            embed.add_field(name="Start", value=f"**{start_timestamp}**", inline=True)
                            if "end" in categorization:
                                end_timestamp = discord.utils.format_dt(discord.utils.parse_time(categorization['end']), style='R')
                                embed.add_field(name="End", value=f"**{end_timestamp}**", inline=True)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Error", description=f"Error: {data['errors']}", color=0xff4545)
                    await ctx.send(embed=embed)
            elif response.status == 400:
                embed = discord.Embed(title="Bad Request", description="The server could not understand the request due to invalid syntax.", color=0xff4545)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Failed to query Cloudflare API", description=f"Status code: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)

    @intel.command(name="asn")
    async def asnintel(self, ctx, asn: int):
        """
        Fetch and display ASN intelligence from Cloudflare.
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/asn/{asn}"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    embed = discord.Embed(title=f"ASN intelligence for {asn}", color=0xfffffe)
                    
                    if "asn" in result:
                        embed.add_field(name="ASN", value=f"**`{result['asn']}`**", inline=False)
                    if "description" in result:
                        embed.add_field(name="Description", value=f"**`{result['description']}`**", inline=False)
                    if "country" in result:
                        embed.add_field(name="Country", value=f"**`{result['country']}`**", inline=False)
                    if "type" in result:
                        embed.add_field(name="Type", value=f"**`{result['type']}`**", inline=False)
                    if "risk_score" in result:
                        embed.add_field(name="Risk Score", value=f"**`{result['risk_score']}`**", inline=False)
                    
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Error: {data['errors']}")
            elif response.status == 400:
                await ctx.send("Bad Request: The server could not understand the request due to invalid syntax.")
            else:
                await ctx.send(f"Failed to query Cloudflare API. Status code: {response.status}")

    @intel.command(name="subnets")
    async def asnsubnets(self, ctx, asn: int):
        """
        Fetch and display ASN subnets intelligence from Cloudflare.
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/asn/{asn}/subnets"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    subnets = result.get("subnets", [])
                    
                    if subnets:
                        pages = [subnets[i:i + 10] for i in range(0, len(subnets), 10)]
                        current_page = 0
                        embed = discord.Embed(title=f"ASN subnets for {asn}", color=0xfffffe)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
                        for subnet in pages[current_page]:
                            embed.add_field(name="Subnet", value=f"**`{subnet}`**", inline=False)
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
                                        embed.clear_fields()
                                        for subnet in pages[current_page]:
                                            embed.add_field(name="Subnet", value=f"**`{subnet}`**", inline=False)
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)

                                    elif str(reaction.emoji) == "◀️" and current_page > 0:
                                        current_page -= 1
                                        embed.clear_fields()
                                        for subnet in pages[current_page]:
                                            embed.add_field(name="Subnet", value=f"**`{subnet}`**", inline=False)
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)

                                    elif str(reaction.emoji) == "❌":
                                        await message.delete()
                                        break

                                except asyncio.TimeoutError:
                                    await message.clear_reactions()
                                    break
                    else:
                        embed = discord.Embed(title=f"ASN subnets for {asn}", color=0xfffffe)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/globe.png")
                        embed.add_field(name="Subnets", value="No subnets found for this ASN.", inline=False)
                        await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Error: {data['errors']}")
            elif response.status == 400:
                await ctx.send("Bad Request: The server could not understand the request due to invalid syntax.")
            else:
                await ctx.send(f"Failed to query Cloudflare API. Status code: {response.status}")
   
    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def emailrouting(self, ctx):
        """Cloudflare Email Routing is designed to simplify the way you create and manage email addresses, without needing to keep an eye on additional mailboxes. Learn more at https://developers.cloudflare.com/email-routing/"""

    @commands.is_owner()
    @emailrouting.command(name="list")
    async def list_email_routing_addresses(self, ctx):
        """List current destination addresses"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        async with self.session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses", headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(title="Error", description=f"Failed to fetch Email Routing addresses: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(title="Error", description="Failed to fetch Email Routing addresses.", color=0xff4545)
                await ctx.send(embed=embed)
                return

            addresses = data.get("result", [])
            if not addresses:
                embed = discord.Embed(title="Email Routing Addresses", description="No Email Routing addresses found.", color=0xff4545)
                await ctx.send(embed=embed)
                return

            pages = [addresses[i:i + 10] for i in range(0, len(addresses), 10)]
            current_page = 0

            embed = discord.Embed(title="Email Routing address list", description="\n".join([f"**`{addr['email']}`**" for addr in pages[current_page]]), color=discord.Color.from_rgb(255, 128, 0))
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
                            embed.description = "\n".join([f"**`{addr['email']}`**" for addr in pages[current_page]])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            embed.description = "\n".join([f"**`{addr['email']}`**" for addr in pages[current_page]])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break

    @commands.is_owner()
    @emailrouting.command(name="add")
    async def create_email_routing_address(self, ctx, email: str):
        """Add a new destination address to your Email Routing service."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email_token = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email_token, api_key, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email_token,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "email": email
        }

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    embed = discord.Embed(title="Destination address added", description="You or the owner of this inbox will need to click the link they were sent just now to enable their email as a destination within your Cloudflare account", color=discord.Color.from_str("#2BBD8E"))
                    embed.add_field(name="Email", value=f"**`{result['email']}`**", inline=False)
                    embed.add_field(name="ID", value=f"**`{result['id']}`**", inline=False)
                    embed.add_field(name="Created", value=f"**`{result['created']}`**", inline=False)
                    embed.add_field(name="Modified", value=f"**`{result['modified']}`**", inline=False)
                    embed.add_field(name="Verified", value=f"**`{result['verified']}`**", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Error: {data['errors']}")
            else:
                await ctx.send(f"Failed to create email routing address. Status code: {response.status}")

    @commands.is_owner()
    @emailrouting.command(name="remove")
    async def remove_email_routing_address(self, ctx, email: str):
        """Remove a destination address from your Email Routing service."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email_token = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email_token, api_key, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        # Query to get the ID of the address to be deleted
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email_token,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch email routing addresses. Status code: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch email routing addresses.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            addresses = data.get("result", [])
            address_id = None
            for address in addresses:
                if address["email"] == email:
                    address_id = address["id"]
                    break

            if not address_id:
                embed = discord.Embed(
                    title="Error",
                    description=f"No email routing address found for **`{email}`**.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

        # Ask for confirmation
        embed = discord.Embed(
            title="Confirm destructive action",
            description=f"**Are you sure you want to remove this email routing address**\n**`{email}`**",
            color=discord.Color.from_str("#ff4545")
        )
        embed.set_footer(text="React to confirm or cancel this request")
        confirmation_message = await ctx.send(embed=embed)
        await confirmation_message.add_reaction("✅")
        await confirmation_message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation_message.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "❌":
                await ctx.send("Email routing address removal cancelled.")
                return
            elif str(reaction.emoji) == "✅":
                # Delete the address
                await asyncio.sleep(5)  # Wait for 5 seconds to avoid rate limiting
                delete_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses/{address_id}"
                async with self.session.delete(delete_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["success"]:
                            embed = discord.Embed(
                                title="Destination address removed",
                                description=f"**Successfully removed email routing address**\n**`{email}`**",
                                color=discord.Color.from_str("#2BBD8E")
                            )
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                title="Error",
                                description=f"**Error:** {data['errors']}",
                                color=discord.Color.from_str("#ff4545")
                            )
                            await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Failed to remove email routing address. Status code: {response.status}",
                            color=discord.Color.from_str("#ff4545")
                        )
                        await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="Confirmation timed out. Email routing address removal cancelled.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @emailrouting.command(name="settings")
    async def get_email_routing_settings(self, ctx):
        """Get and display the current Email Routing settings for a specific zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, account_id, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing"
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch Email Routing settings: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch Email Routing settings.")
                return

            settings = data.get("result", {})
            if not settings:
                await ctx.send("No Email Routing settings found.")
                return

            embed = discord.Embed(
                title="Current settings for Email Routing",
                description=f"**Settings for zone `{zone_identifier.upper()}`**\n\n*Change your zone using `[p]set api cloudflare zone_id`*",
                color=discord.Color.from_rgb(255, 128, 0))  # Cloudflare orange
            created_timestamp = settings.get('created', 'N/A')
            if created_timestamp != 'N/A':
                created_timestamp = f"<t:{int(datetime.fromisoformat(created_timestamp).timestamp())}:F>"
            embed.add_field(name="Created", value=f"**{created_timestamp}**", inline=False)
            embed.add_field(name="Enabled", value=f"**`{settings.get('enabled', 'N/A')}`**", inline=False)
            embed.add_field(name="ID", value=f"**`{settings.get('id', 'N/A').upper()}`**", inline=False)
            modified_timestamp = settings.get('modified', 'N/A')
            if modified_timestamp != 'N/A':
                modified_timestamp = f"<t:{int(datetime.fromisoformat(modified_timestamp).timestamp())}:F>"
            embed.add_field(name="Modified", value=f"**{modified_timestamp}**", inline=False)
            embed.add_field(name="Name", value=f"**`{settings.get('name', 'N/A')}`**", inline=False)
            embed.add_field(name="Skipped wizard", value=f"**`{str(settings.get('skip_wizard', 'N/A')).upper()}`**", inline=False)
            embed.add_field(name="Status", value=f"**`{str(settings.get('status', 'N/A')).upper()}`**", inline=False)
            embed.add_field(name="Synced", value=f"**`{str(settings.get('synced', 'N/A')).upper()}`**", inline=False)
            embed.add_field(name="Tag", value=f"**`{str(settings.get('tag', 'N/A')).upper()}`**", inline=False)

            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @emailrouting.command(name="enable")
    async def enable_email_routing(self, ctx):
        """Enable Email Routing for the selected zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send(
            "Enabling Email Routing will allow Cloudflare to proxy your emails for the selected zone. "
            "This might affect how your emails are delivered. Type `yes` to confirm or `no` to cancel."
        )

        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Confirmation timed out. Email Routing enable operation cancelled.")
            return

        if confirmation.content.lower() != 'yes':
            await ctx.send("Email Routing enable operation cancelled.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/enable"
        async with self.session.post(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to enable Email Routing: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to enable Email Routing.")
                return

            await ctx.send(f"Email Routing has been successfully enabled for zone `{zone_identifier.upper()}`.")
    
    @commands.is_owner()
    @emailrouting.command(name="disable")
    async def disable_email_routing(self, ctx):
        """Disable Email Routing for the selected zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send(
            "Are you sure you want to disable Email Routing? This will stop emails from being proxied by Cloudflare, "
            "and you might miss critical communications. Type `yes` to confirm or `no` to cancel."
        )

        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Confirmation timed out. Email Routing disable operation cancelled.")
            return

        if confirmation.content.lower() != 'yes':
            await ctx.send("Email Routing disable operation cancelled.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/disable"
        async with self.session.post(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to disable Email Routing: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to disable Email Routing.")
                return

            await ctx.send(f"Email Routing has been successfully disabled for zone `{zone_identifier.upper()}`.")
    
    @commands.is_owner()
    @emailrouting.command(name="records")
    async def get_email_routing_dns_records(self, ctx):
        """Get the required DNS records to setup Email Routing"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/dns"
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch DNS records for Email Routing: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch DNS records for Email Routing.")
                return

            records = data.get("result", [])
            if not records:
                await ctx.send("No DNS records found for Email Routing.")
                return

            embed = discord.Embed(title="Email Routing DNS Records", color=discord.Color.from_rgb(255, 128, 0))
            for record in records:
                embed.add_field(
                    name=f"{record['type']} Record",
                    value=f"**Name:** {record['name']}\n**Content:** {record['content']}\n**Priority:** {record.get('priority', 'N/A')}\n**TTL:** {record['ttl']}",
                    inline=False
                )

            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @emailrouting.group(name="rules", invoke_without_command=True)
    async def email_routing_rules(self, ctx):
        """Manage your Email Routing rules"""
        await ctx.send_help(ctx.command)

    @commands.is_owner()
    @email_routing_rules.command(name="add")
    async def add_email_routing_rule(self, ctx, source: str, destination: str):
        """Add a rule to Email Routing"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/rules"
        payload = {
            "source": source,
            "destination": destination
        }

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                await ctx.send(f"Failed to add Email Routing rule: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to add Email Routing rule.")
                return

            await ctx.send(f"Email Routing rule added successfully: {source} -> {destination}")

    @commands.is_owner()
    @email_routing_rules.command(name="remove")
    async def remove_email_routing_rule(self, ctx, rule_id: str):
        """Remove a rule from Email Routing"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/rules/{rule_id}"

        async with self.session.delete(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to remove Email Routing rule: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to remove Email Routing rule.")
                return

            await ctx.send(f"Email Routing rule removed successfully: {rule_id}")

    @commands.is_owner()
    @email_routing_rules.command(name="list")
    async def list_email_routing_rules(self, ctx):
        """Show current Email Routing rules"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/rules"

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch Email Routing rules: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch Email Routing rules.")
                return

            rules = data.get("result", [])
            if not rules:
                await ctx.send("No Email Routing rules found.")
                return

            embed = discord.Embed(title="Email Routing Rules", color=discord.Color.from_rgb(255, 128, 0))
            for rule in rules:
                actions = ", ".join([action["type"] for action in rule["actions"]])
                destinations = ", ".join([value if isinstance(value, str) else str(value) for action in rule["actions"] for value in (action.get("value", []) if isinstance(action.get("value", []), list) else [action.get("value", [])])])
                matchers = ", ".join([f"{matcher.get('field', 'unknown')}: {matcher.get('value', 'unknown')}" for matcher in rule["matchers"]])
                embed.add_field(
                    name=f"Rule ID: {rule['id']}",
                    value=f"**Name:** {rule['name']}\n**Enabled:** {rule['enabled']}\n**Actions:** {actions}\n**Destinations:** {destinations}\n**Matchers:** {matchers}\n**Priority:** {rule['priority']}\n**Tag:** {rule['tag']}",
                    inline=False
                )

            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def hyperdrive(self, ctx):
        """Hyperdrive is a service that accelerates queries you make to existing databases, making it faster to access your data from across the globe, irrespective of your users’ location. Learn more at https://developers.cloudflare.com/hyperdrive/"""
            
    @commands.is_owner()
    @hyperdrive.command(name="list")
    async def list_hyperdrives(self, ctx):
        """List current Hyperdrives in the specified account"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(
                title="Authentication error",
                description="Your bot is missing one or more authentication elements required to interact with your Cloudflare account securely. Please ensure you have set an `api_key`, `email`, `bearer_token`, and `account_id` for this command to function properly. If you're not sure what this error means, ask your systems admin, or a more tech-inclined friend.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs"

        async with self.session.get(url, headers=headers) as response:
            if response.status == 401:
                embed = discord.Embed(
                    title="Upgrade required",
                    description="**Cloudflare Hyperdrive** requires the attached **Cloudflare account** to be subscribed to a **Workers Paid** plan.",
                    color=discord.Color.red()
                )
                button = discord.ui.Button(
                    label="Hyperdrive prerequisites",
                    url="https://developers.cloudflare.com/hyperdrive/get-started/#prerequisites"
                )
                button2 = discord.ui.Button(
                    label="Workers pricing",
                    url="https://developers.cloudflare.com/workers/platform/pricing/#workers"
                )
                view = discord.ui.View()
                view.add_item(button)
                view.add_item(button2)
                await ctx.send(embed=embed, view=view)
                return
            elif response.status != 200:
                await ctx.send(f"Failed to fetch Hyperdrives: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch Hyperdrives.")
                return

            hyperdrives = data.get("result", [])
            if not hyperdrives:
                await ctx.send("No Hyperdrives found.")
                return

            embed = discord.Embed(title="Hyperdrives", color=discord.Color.from_rgb(255, 128, 0))
            for hyperdrive in hyperdrives:
                caching = hyperdrive["caching"]
                origin = hyperdrive["origin"]
                embed.add_field(
                    name=f"Hyperdrive ID: {hyperdrive['id']}",
                    value=(
                        f"**Name:** {hyperdrive['name']}\n"
                        f"**Caching Disabled:** {caching['disabled']}\n"
                        f"**Max Age:** {caching['max_age']} seconds\n"
                        f"**Stale While Revalidate:** {caching['stale_while_revalidate']} seconds\n"
                        f"**Origin Database:** {origin['database']}\n"
                        f"**Origin Host:** {origin['host']}\n"
                        f"**Origin Port:** {origin['port']}\n"
                        f"**Origin Scheme:** {origin['scheme']}\n"
                        f"**Origin User:** {origin['user']}"
                    ),
                    inline=False
                )

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="create")
    async def create_hyperdrive(self, ctx, name: str, password: str, database: str, host: str, port: str, scheme: str, user: str, caching_disabled: bool, max_age: int, stale_while_revalidate: int):
        """Create a new Hyperdrive"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")

        if not all([email, api_key, bearer_token, account_id]):
            await ctx.send("Bearer token or account ID not set.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs"
        payload = {
            "origin": {
                "password": password,
                "database": database,
                "host": host,
                "port": port,
                "scheme": scheme,
                "user": user
            },
            "caching": {
                "disabled": caching_disabled,
                "max_age": max_age,
                "stale_while_revalidate": stale_while_revalidate
            },
            "name": name
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 401:
                embed = discord.Embed(
                    title="Upgrade required",
                    description="**Cloudflare Hyperdrive** requires the attached **Cloudflare account** to be subscribed to a **Workers Paid** plan.",
                    color=discord.Color.red()
                )
                button = discord.ui.Button(
                    label="Hyperdrive prerequisites",
                    url="https://developers.cloudflare.com/hyperdrive/get-started/#prerequisites"
                )
                button2 = discord.ui.Button(
                    label="Workers pricing",
                    url="https://developers.cloudflare.com/workers/platform/pricing/#workers"
                )
                view = discord.ui.View()
                view.add_item(button)
                view.add_item(button2)
                await ctx.send(embed=embed, view=view)
                return
            elif response.status != 200:
                await ctx.send(f"Failed to create Hyperdrive: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to create Hyperdrive.")
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Hyperdrive successfully created", color=discord.Color.green())
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="delete")
    async def delete_hyperdrive(self, ctx, hyperdrive_id: str):
        """Delete a Hyperdrive."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.delete(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to delete Hyperdrive: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to delete Hyperdrive.")
                return

            await ctx.send(f"Hyperdrive {hyperdrive_id} successfully deleted.")

    @commands.is_owner()
    @hyperdrive.command(name="info")
    async def get_hyperdrive_info(self, ctx, hyperdrive_id: str):
        """Fetch information about a specified Hyperdrive by its ID."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                await ctx.send(f"Failed to fetch Hyperdrive info: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch Hyperdrive info.")
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Hyperdrive Information", color=discord.Color.blue())
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="patch")
    async def patch_hyperdrive(self, ctx, hyperdrive_id: str, *, changes: str):
        """Patch a specified Hyperdrive by its ID with provided changes."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            changes_dict = json.loads(changes)
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON format for changes.")
            return

        async with self.session.patch(url, headers=headers, json=changes_dict) as response:
            if response.status != 200:
                await ctx.send(f"Failed to patch Hyperdrive: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to patch Hyperdrive.")
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Patched Hyperdrive Information", color=discord.Color.green())
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="update")
    async def update_hyperdrive(self, ctx, hyperdrive_id: str, changes: str):
        """Update and return the specified Hyperdrive configuration."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            changes_dict = json.loads(changes)
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON format for changes.")
            return

        async with self.session.put(url, headers=headers, json=changes_dict) as response:
            if response.status != 200:
                await ctx.send(f"Failed to update Hyperdrive: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to update Hyperdrive.")
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Updated Hyperdrive Information", color=discord.Color.green())
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def r2(self, ctx):
        """Cloudflare R2 Storage allows developers to store large amounts of unstructured data without the costly egress bandwidth fees associated with typical cloud storage services. Learn more at https://developers.cloudflare.com/r2/"""

    @commands.is_owner()
    @r2.command(name="create")
    async def createbucket(self, ctx, name: str, location_hint: str):
        """Create a new R2 bucket"""
        valid_location_hints = {
            "apac": "Asia-Pacific",
            "eeur": "Eastern Europe",
            "enam": "Eastern North America",
            "weur": "Western Europe",
            "wnam": "Western North America"
        }
        
        if location_hint not in valid_location_hints:
            embed = discord.Embed(title="Invalid Location Hint", color=discord.Color.red())
            embed.add_field(name="Error", value=f"'{location_hint}' is not a valid location hint.", inline=False)
            embed.add_field(name="Valid Location Hints", value="\n".join([f"**`{key}`** for **{value}**" for key, value in valid_location_hints.items()]), inline=False)
            await ctx.send(embed=embed)
            return

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }
        payload = {
            "name": name,
            "locationHint": location_hint
        }

        async with self.session.post(url, headers=headers, json=payload) as response:
            data = await response.json()
            if response.status != 200 or not data.get("success", False):
                errors = data.get("errors", [])
                error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                await ctx.send(f"Failed to create bucket: {error_messages}")
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Bucket Created", color=discord.Color.green())
            embed.add_field(name="Name", value=f"**`{result.get('name')}`**", inline=False)
            embed.add_field(name="Location", value=f"**`{result.get('location')}`**", inline=False)
            embed.add_field(name="Creation Date", value=f"**`{result.get('creation_date')}`**", inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @r2.command(name="delete")
    async def deletebucket(self, ctx, bucket_name: str):
        """Delete a specified R2 bucket"""
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

        embed = discord.Embed(
            title="Confirm R2 bucket deletion",
            description=f"Are you sure you want to delete the bucket **`{bucket_name}`**?\n\n:warning: **This action cannot be undone**.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel.")
        confirmation_message = await ctx.send(embed=embed)
        await confirmation_message.add_reaction("✅")
        await confirmation_message.add_reaction("❌")

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Bucket deletion cancelled due to timeout.")
            return

        if str(reaction.emoji) == "❌":
            await ctx.send("Bucket deletion cancelled.")
            return

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.delete(url, headers=headers) as response:
            data = await response.json()
            if response.status != 200 or not data.get("success", False):
                errors = data.get("errors", [])
                error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                embed = discord.Embed(title="Bucket deletion failed", color=0xff4545)
                embed.add_field(name="Errors", value=f"**`{error_messages}`**", inline=False)
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(title="Bucket deleted successfully", color=discord.Color.from_rgb(43, 189, 142))
            embed.add_field(name="Bucket", value=f"**`{bucket_name}`**", inline=False)
            await ctx.send(embed=embed)

    @commands.is_owner()
    @r2.command(name="info")
    async def getbucket(self, ctx, bucket_name: str):
        """Get info about an R2 bucket"""

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status != 200 or not data.get("success", False):
                    errors = data.get("errors", [])
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                    embed = discord.Embed(title="Failed to fetch bucket info", color=0xff4545)
                    embed.add_field(name="Errors", value=f"**`{error_messages}`**", inline=False)
                    await ctx.send(embed=embed)
                    return

                bucket_info = data.get("result", {})
                if not bucket_info:
                    await ctx.send("No information found for the specified bucket.")
                    return

                embed = discord.Embed(title="Bucket Information", color=discord.Color.from_rgb(255, 145, 68))
                # Customize individual fields
                if "name" in bucket_info:
                    embed.add_field(name="Name", value=f"**`{bucket_info['name']}`**", inline=False)
                if "creation_date" in bucket_info:
                    embed.add_field(name="Creation Date", value=f"**`{bucket_info['creation_date']}`**", inline=False)
                if "location" in bucket_info:
                    embed.add_field(name="Location", value=f"**`{bucket_info['location'].upper()}`**", inline=False)
                if "storage_class" in bucket_info:
                    embed.add_field(name="Storage Class", value=f"**`{bucket_info['storage_class']}`**", inline=False)
                
                await ctx.send(embed=embed)
        except RuntimeError as e:
            await ctx.send(f"An error occurred: {str(e)}")
            return
        
    @commands.is_owner()
    @r2.command(name="stash", help="Upload a file to the specified R2 bucket")
    async def upload_to_bucket(self, ctx, bucket_name: str):
        if not ctx.message.attachments:
            embed = discord.Embed(title="Upload Error", description="Please attach a file to upload.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        attachment = ctx.message.attachments[0]

        # Check file size (300 MB = 300 * 1024 * 1024 bytes)
        max_size = 300 * 1024 * 1024
        if attachment.size > max_size:
            embed = discord.Embed(title="Upload Error", description="File size exceeds the 300 MB limit.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        file_content = await attachment.read()

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{attachment.filename}"
        headers = {
            "Content-Type": "application/octet-stream",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            start_time = time.monotonic()
            async with self.session.put(url, headers=headers, data=file_content) as response:
                end_time = time.monotonic()
                data = await response.json()
                if response.status != 200 or not data.get("success", False):
                    errors = data.get("errors", [])
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                    embed = discord.Embed(title="Failed to upload file", color=0xff4545)
                    embed.add_field(name="Errors", value=f"**`{error_messages}`**", inline=False)
                    await ctx.send(embed=embed)
                    return

                upload_time = end_time - start_time
                embed = discord.Embed(title="File Uploaded Successfully", color=discord.Color.green())
                embed.add_field(name="File Name", value=f"**`{attachment.filename}`**", inline=False)
                embed.add_field(name="Bucket Name", value=f"**`{bucket_name}`**", inline=False)
                def format_file_size(size):
                    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                        if size < 1024.0:
                            return f"**`{size:.2f} {unit}`**"
                        size /= 1024.0
                    return f"**`{size:.2f} PB`**"  # In case the file is extremely large

                embed.add_field(name="File Size", value=format_file_size(attachment.size), inline=False)
                embed.add_field(name="Upload Time", value=f"**`{upload_time:.2f} seconds`**", inline=False)
                await ctx.send(embed=embed)
        except RuntimeError as e:
            embed = discord.Embed(title="Runtime Error", description=f"An error occurred: {str(e)}", color=0xff4545)
            await ctx.send(embed=embed)
            return
        
    @commands.is_owner()
    @r2.command(name="recycle")
    async def delete_file(self, ctx, bucket_name: str, file_name: str):
        """Delete a file by name from an R2 bucket"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        file_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{file_name}"
        try:
            async with self.session.delete(file_url, headers=headers) as delete_response:
                delete_data = await delete_response.json()
                if delete_response.status != 200 or not delete_data.get("success", False):
                    delete_error_messages = "\n".join([error.get("message", "Unknown error") for error in delete_data.get("errors", [])])
                    embed = discord.Embed(
                        title="Failed to delete file",
                        color=0xff4545
                    )
                    embed.add_field(
                        name="Errors",
                        value=f"**`{delete_error_messages}`**",
                        inline=False
                    )
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="File deleted from bucket",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="File name",
                    value=f"**`{file_name}`**",
                    inline=False
                )
                embed.add_field(
                    name="Bucket targeted",
                    value=f"**`{bucket_name}`**",
                    inline=False
                )
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An unexpected error occurred while deleting the file: {str(e)}",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        

    @commands.is_owner()
    @r2.command(name="fetch")
    async def fetch_file(self, ctx, bucket_name: str, file_name: str):
        """Fetch a file from an R2 bucket"""
        api_info = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_info.get("bearer_token")
        email = api_info.get("email")
        api_key = api_info.get("api_key")
        account_id = api_info.get("account_id")
        if not all([bearer_token, email, api_key, account_id]):
            embed = discord.Embed(
                title="API Key Error",
                description="Missing API keys. Please set them using the appropriate command.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{file_name}"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 413:
                    embed = discord.Embed(
                        title="Error",
                        description="413 Payload Too Large (error code: 40005): Request entity too large",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                if response.status != 200:
                    data = await response.json()
                    errors = data.get("errors", [])
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                    embed = discord.Embed(
                        title="Failed to fetch file by name",
                        color=0xff4545
                    )
                    embed.add_field(
                        name="Errors",
                        value=f"**`{error_messages}`**",
                        inline=False
                    )
                    await ctx.send(embed=embed)

                    # Additional logic to fetch by other attributes
                    list_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects"
                    async with self.session.get(list_url, headers=headers) as list_response:
                        if list_response.status == 413:
                            embed = discord.Embed(
                                title="Error",
                                description="413 Payload Too Large (error code: 40005): Request entity too large",
                                color=0xff4545
                            )
                            await ctx.send(embed=embed)
                            return

                        if list_response.status != 200:
                            list_data = await list_response.json()
                            list_errors = list_data.get("errors", [])
                            list_error_messages = "\n".join([error.get("message", "Unknown error") for error in list_errors])
                            embed = discord.Embed(
                                title="Failed to list files in bucket",
                                color=0xff4545
                            )
                            embed.add_field(
                                name="Errors",
                                value=f"**`{list_error_messages}`**",
                                inline=False
                            )
                            await ctx.send(embed=embed)
                            return

                        list_data = await list_response.json()
                        objects = list_data.get("result", {}).get("objects", [])
                        for obj in objects:
                            if obj.get("name") == file_name:
                                file_url = obj.get("url")
                                async with self.session.get(file_url, headers=headers) as file_response:
                                    if file_response.status == 413:
                                        embed = discord.Embed(
                                            title="Error",
                                            description="413 Payload Too Large (error code: 40005): Request entity too large",
                                            color=0xff4545
                                        )
                                        await ctx.send(embed=embed)
                                        return

                                    if file_response.status == 200:
                                        file_size = int(file_response.headers.get("Content-Length", 0))
                                        if file_size > 100 * 1024 * 1024:  # 100 MB
                                            embed = discord.Embed(
                                                title="File too large",
                                                description="The file size exceeds the 100 MB limit.",
                                                color=0xff4545
                                            )
                                            await ctx.send(embed=embed)
                                            return

                                        file_content = await file_response.read()
                                        embed = discord.Embed(
                                            title="File fetched from bucket",
                                            color=discord.Color.from_rgb(43, 189, 142))
                                        embed.add_field(
                                            name="File name",
                                            value=f"**`{file_name}`**",
                                            inline=False
                                        )
                                        embed.add_field(
                                            name="Bucket targeted",
                                            value=f"**`{bucket_name}`**",
                                            inline=False
                                        )
                                        await ctx.send(embed=embed)
                                        await ctx.send(file=discord.File(io.BytesIO(file_content), filename=file_name))
                                        return

                        embed = discord.Embed(
                            title="File not found",
                            description="The file could not be found by name or other attributes.",
                            color=0xff4545
                        )
                        await ctx.send(embed=embed)
                        return

                file_size = int(response.headers.get("Content-Length", 0))
                if file_size > 100 * 1024 * 1024:  # 100 MB
                    embed = discord.Embed(
                        title="File too large",
                        description="**`The file size exceeds the 100 MB limit`**",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                file_content = await response.read()
                embed = discord.Embed(
                    title="File fetched from bucket",
                    color=discord.Color.from_rgb(43, 189, 142))
                embed.add_field(
                    name="File name",
                    value=f"**`{file_name}`**",
                    inline=False
                )
                embed.add_field(
                    name="Bucket targeted",
                    value=f"**`{bucket_name}`**",
                    inline=False
                )
                await ctx.send(embed=embed)
                await ctx.send(file=discord.File(io.BytesIO(file_content), filename=file_name))
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
