import re
import discord #type: ignore
from redbot.core import commands, Config #type: ignore

class InfoControl(commands.Cog):
    """Detect and remove potentially sensitive information from chat."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled": True,
            "block_email": True,
            "block_ssn": True,
            "block_bankcard": True,
            "block_phone": True,
            "block_ipv4": True,
            "block_ipv6": True,
            "block_creditcard": True,
            "block_passport": True,
            "block_iban": True,
            "block_mac_address": True,
            "block_bitcoin_address": True,
            "block_swift_code": True,
            "block_drivers_license": True,
            "block_vin": True,
            "block_ssn_alternative": True,
            "block_phone_alternative": True,
            "block_zip_code": True,
            "block_street_address": True,
            "block_birthdate": True,
            "patterns": {
                "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
                "bankcard": r"\b\d{4} \d{4} \d{4} \d{4}\b",
                "phone": r"\b\d{5}-\d{5}\b",
                "ipv4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
                "ipv6": r"\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
                "creditcard": r"\b(?:\d[ -]*?){13,16}\b",
                "passport": r"\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b",
                "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",
                "mac_address": r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
                "bitcoin_address": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
                "swift_code": r"\b[A-Z]{4}[A-Z]{2}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3})?\b",
                "drivers_license": r"\b[A-Z]{1,2}\d{1,14}\b",
                "vin": r"\b[A-HJ-NPR-Z0-9]{17}\b",
                "ssn_alternative": r"\b\d{3}\s?\d{2}\s?\d{4}\b",
                "phone_alternative": r"\b\(\d{3}\)\s?\d{3}-\d{4}\b",
                "zip_code": r"\b\d{5}(?:[-\s]\d{4})?\b",
                "street_address": r"\b\d{1,5}\s\w+\s\w+\b",
                "birthdate": r"\b\d{2}/\d{2}/\d{4}\b"
            }
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild = message.guild
        if not guild:
            return

        guild_config = await self.config.guild(guild).all()
        if not guild_config["enabled"]:
            return

        for key, pattern in guild_config["patterns"].items():
            if guild_config.get(f"block_{key}", False) and re.search(pattern, message.content):
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, your message contained sensitive information and was removed.")
                except Exception as e:
                    await message.channel.send(f"Failed to delete message: {e}")
                break

    @commands.group()
    @commands.guild_only()
    async def infocontrol(self, ctx):
        """Manage info enforcement settings."""
        pass

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def enable(self, ctx):
        """Enable info enforcement"""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Info enforcement is now enabled.")

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def disable(self, ctx):
        """Disable info enforcement"""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Info enforcement is now disabled.")

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def toggle(self, ctx, data_type: str):
        """Toggle blocking of a specific data type."""
        valid_types = [
            "email", "ssn", "bankcard", "phone", "ipv4", "ipv6", "creditcard", 
            "passport", "iban", "mac_address", "bitcoin_address", "swift_code", 
            "drivers_license", "vin", "ssn_alternative", "phone_alternative"
        ]
        if data_type not in valid_types:
            await ctx.send(f"Invalid data type. Valid types are: {', '.join(valid_types)}")
            return

        current = await self.config.guild(ctx.guild).get_raw(f"block_{data_type}")
        await self.config.guild(ctx.guild).set_raw(f"block_{data_type}", value=not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Blocking for {data_type} is now {status}.")


    @infocontrol.command()
    async def settings(self, ctx):
        """List current settings for blocking data types."""
        guild_config = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(title="Current info control settings", color=0xfffffe)
        
        key_transform = {
            "block_email": "Email",
            "block_ssn": "SSN",
            "block_bankcard": "Bank card",
            "block_phone": "Phone",
            "block_ipv4": "IPv4 address",
            "block_ipv6": "IPv6 address",
            "block_creditcard": "Credit card",
            "block_passport": "Passport",
            "block_iban": "IBAN",
            "block_mac_address": "MAC address",
            "block_bitcoin_address": "Bitcoin address",
            "block_swift_code": "SWIFT code",
            "block_drivers_license": "Driver's license",
            "block_vin": "Vehicle ID (VIN)",
            "block_ssn_alternative": "SSN alternative",
            "block_phone_alternative": "Phone alternative",
            "block_zip_code": "Zip code",
            "block_street_address": "Street address",
            "block_birthdate": "Birth date",
        }
        
        for key, value in guild_config.items():
            if key.startswith("block_"):
                human_readable_key = key_transform.get(key, key)
                embed.add_field(name=human_readable_key, value='**Active**' if value else 'Inactive', inline=True)
        
        await ctx.send(embed=embed)
