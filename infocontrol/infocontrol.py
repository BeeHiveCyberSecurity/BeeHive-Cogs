import re
import discord #type: ignore
from redbot.core import commands, Config #type: ignore

class InfoControl(commands.Cog):
    """Detect and remove potentially sensitive information from chat."""
    
    __version__ = "1.0.5"

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
            "block_phone_no_spaces": True,
            "block_zip_code": True,
            "block_street_address": True,
            "block_birthdate": True,
            "block_national_id": True,
            "block_tax_id": True,
            "block_medical_id": True,
            "block_student_id": True,
            "block_license_plate": True,
            "log_channel": None,
            "moderator_roles": [],
            "patterns": {
                "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
                "bankcard": r"\b\d{4} \d{4} \d{4} \d{4}\b",
                "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
                "phone_no_spaces": r"\b\d{10}\b",
                "ipv4": r"\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
                "ipv6": r"\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
                "creditcard": r"\b(?:\d[ -]*?){13,19}\b",
                "passport": r"\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b",
                "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",
                "mac_address": r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
                "bitcoin_address": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
                "swift_code": r"\b[A-Z]{4}[A-Z]{2}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3})?\b",
                "drivers_license": r"\b[A-Z]{1,2}\d{1,14}\b",
                "vin": r"\b[A-HJ-NPR-Z0-9]{17}\b",
                "ssn_alternative": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
                "phone_alternative": r"\b\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b",
                "zip_code": r"\b\d{5}(?:[-\s]\d{4})?\b",
                "street_address": r"\b\d{1,5}\s(?:[A-Za-z0-9#]+\s?){1,5}\b",
                "birthdate": r"\b\d{2}/\d{2}/\d{4}\b",
                "national_id": r"\b[A-Z0-9]{9}\b",
                "tax_id": r"\b\d{2}-\d{7}\b",
                "medical_id": r"\b[A-Z0-9]{10}\b",
                "student_id": r"\b[A-Z0-9]{8}\b",
                "license_plate": r"\b[A-Z0-9]{1,7}\b"
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
                    embed = discord.Embed(
                        title="Message removed",
                        description=f"{message.author.mention}, your message contained a match for one or more potential categories and was removed as a precaution.",
                        color=0xff4545
                    )
                    await message.channel.send(embed=embed)

                    # Log the deletion if log_channel is set
                    log_channel_id = guild_config.get("log_channel")
                    if log_channel_id:
                        log_channel = self.bot.get_channel(log_channel_id)
                        if log_channel:
                            log_embed = discord.Embed(
                                title="Sensitive content matched and removed",
                                description=f"A message from {message.author.mention} was removed in {message.channel.mention} due to containing potentially sensitive information.",
                                color=0xff4545
                            )
                            log_embed.add_field(name="Author", value=message.author.mention, inline=True)
                            log_embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                            log_embed.add_field(name="Pattern matched", value=f"`{key}`", inline=True)
                            log_embed.add_field(name="Message content", value="```{}```".format(message.content.replace('```', '`\u200b``')), inline=False)
                            log_embed.set_footer(text=f"Message ID: {message.id} | Author ID: {message.author.id}")
                            
                            # Mention moderator roles if any are set
                            moderator_roles = guild_config.get("moderator_roles", [])
                            if moderator_roles:
                                mentions = " ".join([f"<@&{role_id}>" for role_id in moderator_roles])
                                await log_channel.send(content=mentions, embed=log_embed, allowed_mentions=discord.AllowedMentions(roles=True))
                            else:
                                await log_channel.send(embed=log_embed)

                except Exception as e:
                    embed = discord.Embed(
                        title="Error",
                        description=f"Failed to delete message: {e}",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=embed)
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
            "email", "ssn", "bankcard", "phone", "phone_no_spaces", "ipv4", "ipv6", "creditcard", 
            "passport", "iban", "mac_address", "bitcoin_address", "swift_code", 
            "drivers_license", "vin", "ssn_alternative", "phone_alternative",
            "zip_code", "street_address", "birthdate", "national_id", "tax_id", "medical_id", "student_id", "license_plate"
        ]
        if data_type not in valid_types:
            embed = discord.Embed(
                title="Invalid check",
                description=f"Valid types are: {', '.join(valid_types)}",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        current = await self.config.guild(ctx.guild).get_raw(f"block_{data_type}")
        await self.config.guild(ctx.guild).set_raw(f"block_{data_type}", value=not current)
        status = "enabled" if not current else "disabled"
        embed = discord.Embed(
            title="Blocking toggled",
            description=f"Blocking for `{data_type}` is now **{status}**.",
            color=0x2bbd8e if status == "enabled" else 0xff4545
        )
        await ctx.send(embed=embed)

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def alerts(self, ctx, channel: discord.TextChannel):
        """Set the log channel for info control deletions."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}.")

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def addmodrole(self, ctx, role: discord.Role):
        """Add a role to the list of roles to mention in alerts."""
        async with self.config.guild(ctx.guild).moderator_roles() as mod_roles:
            if role.id not in mod_roles:
                mod_roles.append(role.id)
                await ctx.send(f"Role {role.mention} added to the list of roles to mention in alerts.")
            else:
                await ctx.send(f"Role {role.mention} is already in the list of roles to mention in alerts.")

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def removemodrole(self, ctx, role: discord.Role):
        """Remove a role from the list of roles to mention in alerts."""
        async with self.config.guild(ctx.guild).moderator_roles() as mod_roles:
            if role.id in mod_roles:
                mod_roles.remove(role.id)
                await ctx.send(f"Role {role.mention} removed from the list of roles to mention in alerts.")
            else:
                await ctx.send(f"Role {role.mention} is not in the list of roles to mention in alerts.")

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
            "block_phone_no_spaces": "Phone (no spaces)",
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
            "block_national_id": "National ID",
            "block_tax_id": "Tax ID",
            "block_medical_id": "Medical ID",
            "block_student_id": "Student ID",
            "block_license_plate": "License Plate"
        }
        
        for key, value in guild_config.items():
            if key.startswith("block_"):
                human_readable_key = key_transform.get(key, key)
                embed.add_field(name=human_readable_key, value='**Active**' if value else 'Inactive', inline=True)
        
        log_channel_id = guild_config.get("log_channel")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            embed.add_field(name="Alert channel", value=log_channel.mention if log_channel else "Not found", inline=False)
        else:
            embed.add_field(name="Alert channel", value="Not set", inline=False)
        
        embed.set_footer(text=f"Version {self.__version__}")
        
        await ctx.send(embed=embed)
