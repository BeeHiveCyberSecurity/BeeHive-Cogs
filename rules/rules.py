import discord
from redbot.core import commands, Config
import asyncio

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "acceptance_role_id": None,
            "rules_channel_id": None
        }
        self.config.register_guild(**default_guild)

    @commands.group(name='rules', invoke_without_command=True)
    @commands.admin_or_permissions()
    async def rules_group(self, ctx):
        """Group command for managing server rules."""
        await ctx.send_help(ctx.command)

    @rules_group.command(name='send')
    async def send_rules(self, ctx):
        """Send the server rules to the configured rules channel or current channel."""
        rules_channel_id = await self.config.guild(ctx.guild).rules_channel_id()
        channel = ctx.guild.get_channel(rules_channel_id) if rules_channel_id else ctx.channel

        rules = [
            "### Rule 1: Be respectful to everyone.\n> **1.1** Treat all members with kindness and consideration. Personal attacks, harassment, and bullying will not be tolerated.",
            "### Rule 2: No spamming or flooding the chat.\n> **2.1** Avoid sending repetitive messages, excessive emojis, or large blocks of text that disrupt the flow of conversation.",
            "### Rule 3: No hate speech or offensive language.\n> **3.1** This includes any form of discrimination, racism, sexism, homophobia, or any other form of hate speech.",
            "### Rule 4: Keep conversations in the appropriate channels.\n> **4.1** Use the designated channels for specific topics to keep discussions organized and relevant.",
            "### Rule 5: Follow the Discord Community Guidelines.\n> **5.1** Ensure that your behavior and content comply with Discord's official guidelines, which can be found at https://discord.com/guidelines.",
            "### Rule 6: Listen to the moderators and admins.\n> **6.1** They are here to help maintain a safe and enjoyable environment. Follow their instructions and respect their decisions.",
            "### Rule 7: Do not share dangerous or malicious content.\n> **7.1** This includes links to phishing sites, malware, or any other harmful material.",
            "### Rule 8: Do not share personal information.\n> **8.1** Protect your privacy and the privacy of others by not sharing personal details such as addresses, phone numbers, or any other sensitive information.",
            "### Rule 9: Use appropriate usernames and avatars.\n> **9.1** Usernames and avatars should not be offensive, inappropriate, or disruptive to the community.",
            "### Rule 10: No self-promotion or advertising.\n> **10.1** Do not promote your own content, services, or servers without permission from the moderators.",
            "### Rule 11: No excessive shitposting.\n> **11.1** Keep the content meaningful and avoid posting low-effort or irrelevant content excessively.",
            "### Rule 12: Staff have the final decision for all moderative actions.\n> **12.1** Even if an action is not in clear violation of a rule, staff decisions are to be respected and followed."
        ]
        for rule in rules:
            embed = discord.Embed(description=rule, color=0xfffffe)
            await channel.send(embed=embed)
            await asyncio.sleep(2)

    @rules_group.command(name='setacceptancerole')
    @commands.has_permissions(manage_roles=True)
    async def set_acceptance_role(self, ctx, role: discord.Role):
        """Set the role to be given when a user accepts the rules."""
        await self.config.guild(ctx.guild).acceptance_role_id.set(role.id)
        await ctx.send(f"Acceptance role set to: {role.name}")

    @rules_group.command(name='setruleschannel')
    @commands.has_permissions(manage_channels=True)
    async def set_rules_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where rules will be sent."""
        await self.config.guild(ctx.guild).rules_channel_id.set(channel.id)
        await ctx.send(f"Rules channel set to: {channel.mention}")

    @rules_group.command(name='sendacceptmsg')
    async def send_accept_message(self, ctx):
        """Send a message for users to accept the rules."""
        acceptance_role_id = await self.config.guild(ctx.guild).acceptance_role_id()
        if acceptance_role_id is None:
            await ctx.send("Acceptance role not set. Use the setacceptancerole command first.")
            return

        embed = discord.Embed(
            description="By reacting, you indicate you've read and agree to the rules.",
            color=0xfffffe
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")

        def check(reaction, user):
            return (
                str(reaction.emoji) == "✅"
                and reaction.message.id == message.id
                and not user.bot
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
                role = ctx.guild.get_role(acceptance_role_id)
                if role:
                    try:
                        await user.add_roles(role)
                        try:
                            await user.send("Thank you for accepting the rules. Please remember that failing to follow them will result in moderation.")
                        except discord.Forbidden:
                            pass  # If we can't DM the user, just pass silently
                    except discord.Forbidden:
                        await ctx.send(f"Failed to assign role to {user.mention}. Check bot permissions.")
            except asyncio.TimeoutError:
                break

