from redbot.core import commands, Config
from redbot.core.bot import Red
import discord

class EasyRules(commands.Cog):
    """A cog for easy rule management using Discord interactions."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "rules": {
                "1": {"text": "Be respectful to other members.", "enabled": True},
                "2": {"text": "No spamming or flooding the chat with messages.", "enabled": True},
                # Add more default rules here with unique keys and enabled set to True or False
            }
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(name="setrules", invoke_without_command=True)
    async def _set_rules(self, ctx: commands.Context, channel: discord.TextChannel):
        """Send selected pre-written rules to a specific channel."""
        rules = await self.config.guild(ctx.guild).rules()
        embed = discord.Embed(title="Server Rules", color=discord.Color.blue())
        for rule_number, rule_data in rules.items():
            if rule_data["enabled"]:
                embed.add_field(name=f"Rule {rule_number}", value=rule_data["text"], inline=False)
        await channel.send(embed=embed)
        await ctx.send(f"Rules have been sent to {channel.mention}")

    @_set_rules.command(name="add")
    async def _set_rules_add(self, ctx: commands.Context, *, rule: str):
        """Add a new rule to the list of pre-written rules."""
        async with self.config.guild(ctx.guild).rules() as rules:
            rule_number = str(len(rules) + 1)
            rules[rule_number] = {"text": rule, "enabled": True}
        await ctx.send("New rule added.")

    @_set_rules.command(name="edit")
    async def _set_rules_edit(self, ctx: commands.Context, rule_number: int, *, new_text: str):
        """Edit an existing rule."""
        async with self.config.guild(ctx.guild).rules() as rules:
            str_rule_number = str(rule_number)
            if str_rule_number in rules:
                rules[str_rule_number]["text"] = new_text
                await ctx.send(f"Rule {rule_number} has been updated.")
            else:
                await ctx.send("Rule number does not exist.")

    @_set_rules.command(name="toggle")
    async def _set_rules_toggle(self, ctx: commands.Context, rule_number: int):
        """Toggle a rule's enabled state."""
        async with self.config.guild(ctx.guild).rules() as rules:
            str_rule_number = str(rule_number)
            if str_rule_number in rules:
                rules[str_rule_number]["enabled"] = not rules[str_rule_number]["enabled"]
                state = "enabled" if rules[str_rule_number]["enabled"] else "disabled"
                await ctx.send(f"Rule {rule_number} has been {state}.")
            else:
                await ctx.send("Rule number does not exist.")

    @_set_rules.command(name="remove")
    async def _set_rules_remove(self, ctx: commands.Context, rule_number: int):
        """Remove a rule from the list of pre-written rules."""
        async with self.config.guild(ctx.guild).rules() as rules:
            str_rule_number = str(rule_number)
            if str_rule_number in rules:
                del rules[str_rule_number]
                await ctx.send("Rule removed.")
            else:
                await ctx.send("Invalid rule number.")
                
    @_set_rules.command(name="list")
    async def _set_rules_list(self, ctx: commands.Context):
        """List all rules with their number and state."""
        rules = await self.config.guild(ctx.guild).rules()
        if rules:
            embed = discord.Embed(title="List of Server Rules", color=discord.Color.green())
            for rule_number, rule_data in rules.items():
                state = "Enforced" if rule_data["enabled"] else "Unenforced"
                embed.add_field(name=f"Rule {rule_number}", value=f"{rule_data['text']} - {state}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No rules have been set.")

def setup(bot: Red):
    cog = EasyRules(bot)
    bot.add_cog(cog)


