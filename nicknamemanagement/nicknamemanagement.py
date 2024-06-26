import discord
from redbot.core import commands, Config, checks

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

        try:
            await member.edit(nick=purified_nickname)
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

        try:
            await member.edit(nick=normalized_nickname)
            await ctx.send(f"{member.mention}'s nickname has been normalized to: {normalized_nickname}")
        except discord.Forbidden:
            await ctx.send("I do not have permission to change that member's nickname.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred: {e}")

    @nickname.command()
    async def set_allowed_characters(self, ctx, *, characters: str):
        """Set the allowed characters for nicknames."""
        await self.config.guild(ctx.guild).allowed_characters.set(characters)
        await ctx.send(f"Allowed characters set to: {characters}")

    @nickname.command()
    async def set_max_length(self, ctx, length: int):
        """Set the maximum length for nicknames."""
        await self.config.guild(ctx.guild).max_length.set(length)
        await ctx.send(f"Maximum nickname length set to: {length}")

    @nickname.command()
    async def set_auto_purify(self, ctx, enable: bool):
        """Enable or disable auto-purification of nicknames."""
        await self.config.guild(ctx.guild).auto_purify.set(enable)
        status = "enabled" if enable else "disabled"
        await ctx.send(f"Auto-purification has been {status}.")

    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            guild_settings = await self.config.guild(after.guild).all()
            if guild_settings["auto_purify"]:
                allowed_characters = guild_settings["allowed_characters"]
                purified_nickname = ''.join(c for c in after.display_name if c in allowed_characters)
                purified_nickname = purified_nickname[:guild_settings["max_length"]]
                try:
                    await after.edit(nick=purified_nickname)
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

def setup(bot):
    bot.add_cog(NicknameManagement(bot))
