import discord
from redbot.core import commands, Config, checks
import asyncio

class NicknameManagement(commands.Cog):
    """Cog for managing and normalizing user nicknames."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "allowed_characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
            "max_length": 32,
            "auto_purify": False
        }
        self.config.register_guild(**default_guild)
        self.bot.add_listener(self.on_member_update, "on_member_update")
        self.bot.add_listener(self.on_member_join, "on_member_join")
        self.bot.loop.create_task(self.cleanup_nicknames())

    @commands.guild_only()
    @commands.admin()
    @commands.group()
    async def nickname(self, ctx):
        """Group command for nickname management."""
        pass

    @nickname.command()
    async def purify(self, ctx, member: discord.Member):
        """Purify a member's nickname to allowed characters only."""
        guild_settings = await self.config.guild(ctx.guild).all()
        allowed_characters = guild_settings["allowed_characters"]
        purified_nickname = ''.join(c for c in member.display_name if c in allowed_characters)
        purified_nickname = purified_nickname[:guild_settings["max_length"]]

        if not purified_nickname:
            purified_nickname = ''.join(c for c in member.name if c in allowed_characters)
            purified_nickname = purified_nickname[:guild_settings["max_length"]]

        try:
            await member.edit(nick=purified_nickname, reason="Nickname purified to allowed characters")
            await ctx.send(f"{member.mention}'s nickname has been purified to: {purified_nickname}")
        except discord.Forbidden:
            await ctx.send("I do not have permission to change that member's nickname.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred: {e}")

    @nickname.command()
    async def normalize(self, ctx, member: discord.Member):
        """Normalize a member's nickname to a standard format."""
        guild_settings = await self.config.guild(ctx.guild).all()
        allowed_characters = guild_settings["allowed_characters"]
        normalized_nickname = ''.join(c for c in member.display_name if c in allowed_characters).title()
        normalized_nickname = normalized_nickname[:guild_settings["max_length"]]

        if not normalized_nickname:
            normalized_nickname = ''.join(c for c in member.name if c in allowed_characters).title()
            normalized_nickname = normalized_nickname[:guild_settings["max_length"]]

        try:
            await member.edit(nick=normalized_nickname, reason="Nickname normalized to standard format")
            await ctx.send(f"{member.mention}'s nickname has been normalized to: {normalized_nickname}")
        except discord.Forbidden:
            await ctx.send("I do not have permission to change that member's nickname.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred: {e}")

    @nickname.command()
    async def allowedchars(self, ctx, *, characters: str):
        """Set the allowed characters for nicknames."""
        await self.config.guild(ctx.guild).allowed_characters.set(characters)
        await ctx.send(f"Allowed characters set to: {characters}")

    @nickname.command()
    async def maxlength(self, ctx, length: int):
        """Set the maximum length for nicknames."""
        await self.config.guild(ctx.guild).max_length.set(length)
        await ctx.send(f"Maximum nickname length set to: {length}")

    @nickname.command()
    async def autopurify(self, ctx, enable: bool):
        """Enable or disable auto-purification of nicknames."""
        await self.config.guild(ctx.guild).auto_purify.set(enable)
        status = "enabled" if enable else "disabled"
        await ctx.send(f"Auto-purification has been {status}.")

    @nickname.command()
    async def cleanup(self, ctx):
        """Clean up all pre-existing nicknames in the server slowly to prevent rate limits."""
        await ctx.send("Starting nickname cleanup. This may take a while...")
        guild_settings = await self.config.guild(ctx.guild).all()
        allowed_characters = guild_settings["allowed_characters"]
        max_length = guild_settings["max_length"]

        total_members = len(ctx.guild.members)
        processed_members = 0
        changed_nicknames = 0
        failed_changes = 0
        character_removal_count = {}

        embed = discord.Embed(title="Nickname cleanup in progress", color=0xfffffe)
        embed.add_field(name="Total members", value=total_members, inline=True)
        embed.add_field(name="Processed members", value=processed_members, inline=True)
        embed.add_field(name="Changed nicknames", value=changed_nicknames, inline=True)
        embed.add_field(name="Failed changes", value=failed_changes, inline=True)
        progress_message = await ctx.send(embed=embed)

        for member in ctx.guild.members:
            if member.bot:
                try:
                    await member.edit(nick=None, reason="Clearing bot nickname to restore original name")
                    changed_nicknames += 1
                    await asyncio.sleep(1)  # Sleep to prevent hitting rate limits
                except discord.Forbidden:
                    failed_changes += 1
                except discord.HTTPException:
                    failed_changes += 1
            else:
                original_nickname = member.display_name
                purified_nickname = ''.join(c for c in original_nickname if c in allowed_characters)
                purified_nickname = purified_nickname[:max_length]
                if not purified_nickname:
                    purified_nickname = ''.join(c for c in member.name if c in allowed_characters)
                    purified_nickname = purified_nickname[:max_length]

                removed_characters = set(original_nickname) - set(purified_nickname)
                for char in removed_characters:
                    if char in character_removal_count:
                        character_removal_count[char] += 1
                    else:
                        character_removal_count[char] = 1

                if original_nickname != purified_nickname:
                    try:
                        await member.edit(nick=purified_nickname, reason="Nickname purified during cleanup")
                        changed_nicknames += 1
                        await asyncio.sleep(1)  # Sleep to prevent hitting rate limits
                    except discord.Forbidden:
                        failed_changes += 1
                    except discord.HTTPException:
                        failed_changes += 1

            processed_members += 1
            if processed_members % 100 == 0:
                embed.set_field_at(1, name="Processed members", value=processed_members, inline=True)
                embed.set_field_at(2, name="Changed nicknames", value=changed_nicknames, inline=True)
                embed.set_field_at(3, name="Failed changes", value=failed_changes, inline=True)
                await progress_message.edit(embed=embed)

        most_removed_characters = sorted(character_removal_count.items(), key=lambda item: item[1], reverse=True)[:5]
        most_removed_characters_str = ', '.join([f"{char}: {count}" for char, count in most_removed_characters])

        embed = discord.Embed(title="Nickname cleanup finished", color=discord.Color.green())
        embed.add_field(name="Total members", value=total_members, inline=True)
        embed.add_field(name="Processed members", value=processed_members, inline=True)
        embed.add_field(name="Changed nicknames", value=changed_nicknames, inline=True)
        embed.add_field(name="Failed changes", value=failed_changes, inline=True)
        embed.add_field(name="Most removed characters", value=most_removed_characters_str, inline=False)
        await progress_message.edit(embed=embed)

    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            guild_settings = await self.config.guild(after.guild).all()
            if guild_settings["auto_purify"]:
                allowed_characters = guild_settings["allowed_characters"]
                purified_nickname = ''.join(c for c in after.display_name if c in allowed_characters)
                purified_nickname = purified_nickname[:guild_settings["max_length"]]
                if not purified_nickname:
                    purified_nickname = ''.join(c for c in after.name if c in allowed_characters)
                    purified_nickname = purified_nickname[:guild_settings["max_length"]]
                try:
                    await after.edit(nick=purified_nickname, reason="Nickname auto-purified on update")
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

    async def on_member_join(self, member):
        guild_settings = await self.config.guild(member.guild).all()
        if guild_settings["auto_purify"]:
            allowed_characters = guild_settings["allowed_characters"]
            purified_nickname = ''.join(c for c in member.display_name if c in allowed_characters)
            purified_nickname = purified_nickname[:guild_settings["max_length"]]
            if not purified_nickname:
                purified_nickname = ''.join(c for c in member.name if c in allowed_characters)
                purified_nickname = purified_nickname[:guild_settings["max_length"]]
            try:
                await member.edit(nick=purified_nickname, reason="Nickname auto-purified on join")
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

    async def cleanup_nicknames(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                guild_settings = await self.config.guild(guild).all()
                if guild_settings["auto_purify"]:
                    allowed_characters = guild_settings["allowed_characters"]
                    max_length = guild_settings["max_length"]
                    for member in guild.members:
                        purified_nickname = ''.join(c for c in member.display_name if c in allowed_characters)
                        purified_nickname = purified_nickname[:max_length]
                        if not purified_nickname:
                            purified_nickname = ''.join(c for c in member.name if c in allowed_characters)
                            purified_nickname = purified_nickname[:max_length]
                        if member.display_name != purified_nickname:
                            try:
                                await member.edit(nick=purified_nickname, reason="Nickname auto-purified during cleanup")
                            except discord.Forbidden:
                                pass
                            except discord.HTTPException:
                                pass
            await asyncio.sleep(3600)  # Run the cleanup task every hour
