import re
import discord #type: ignore
import asyncio
from redbot.core import commands, Config #type: ignore

class InfoControl(commands.Cog):
    """Detect and remove potentially sensitive information from chat."""
    
    __version__ = "1.0.5"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.default_guild = {
            "enabled": True,
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
                "creditcard": r"\b(?:\d[ -]?){13,19}\b",
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
                "student_id": r"\b[A-Z0-9]{8}\b",
                "license_plate": r"\b[A-Z0-9]{6,7}\b"
            }
        }
        self.default_guild.update({f"block_{key}": True for key in self.default_guild["patterns"].keys()})
        self.config.register_guild(**self.default_guild)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.mentions:
            return
        if any(mention in message.content for mention in message.mentions):
            return

        guild_config = await self.config.guild(message.guild).all()
        if not guild_config["enabled"]:
            return

        for key, pattern in guild_config["patterns"].items():
            if guild_config.get(f"block_{key}", False) and re.search(pattern, message.content):
                await self.handle_message_deletion(message, key, guild_config)
                break

    async def handle_message_deletion(self, message, key, guild_config):
        try:
            await message.delete()
            embed = discord.Embed(
                title="Message removed",
                description=f"{message.author.mention}, your message contained a match for one or more potential categories and was removed as a precaution.",
                color=0xff4545
            )
            await message.channel.send(embed=embed)

            log_channel_id = guild_config.get("log_channel")
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await self.log_deletion(message, key, log_channel, guild_config)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to delete message: {e}",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)

    async def log_deletion(self, message, key, log_channel, guild_config):
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

        moderator_roles = guild_config.get("moderator_roles", [])
        if moderator_roles:
            mentions = " ".join([f"<@&{role_id}>" for role_id in moderator_roles])
            await log_channel.send(content=mentions, embed=log_embed, allowed_mentions=discord.AllowedMentions(roles=True))
        else:
            await log_channel.send(embed=log_embed)

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
        valid_types = list(self.default_guild["patterns"].keys())
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
            "block_student_id": "Student ID",
            "block_license_plate": "License Plate"
        }
        
        settings_list = [(key_transform.get(key, key), '**Active**' if value else 'Inactive') for key, value in guild_config.items() if key.startswith("block_")]
        
        log_channel_id = guild_config.get("log_channel")
        log_channel_value = self.bot.get_channel(log_channel_id).mention if log_channel_id and self.bot.get_channel(log_channel_id) else "Not set"
        
        settings_list.append(("Alert channel", log_channel_value))
        
        pages = [settings_list[i:i + 9] for i in range(0, len(settings_list), 9)]
        
        current_page = 0
        total_pages = len(pages)
        
        def create_embed(page):
            embed = discord.Embed(title="Current info control settings", color=0xfffffe)
            for name, value in page:
                embed.add_field(name=name, value=value, inline=True)
            embed.set_footer(text=f"Page {current_page + 1}/{total_pages} | Version {self.__version__}")
            return embed
        
        message = await ctx.send(embed=create_embed(pages[current_page]))
        
        if total_pages > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id
            
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "➡️" and current_page < total_pages - 1:
                        current_page += 1
                        await message.edit(embed=create_embed(pages[current_page]))
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=create_embed(pages[current_page]))
                    
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break

    @commands.admin_or_permissions()
    @infocontrol.command()
    async def cleanup(self, ctx):
        """Cleanup the config and remove no longer used patterns."""
        guild_config = await self.config.guild(ctx.guild).all()
        valid_patterns = set(self.default_guild["patterns"].keys())
        keys_to_remove = [key for key in guild_config.keys() if key.startswith("block_") and key[6:] not in valid_patterns]

        for key in keys_to_remove:
            await self.config.guild(ctx.guild).clear_raw(key)

        await ctx.send(f"Removed {len(keys_to_remove)} no longer used patterns from the config.")
