import discord
from redbot.core import commands, Config
import asyncio

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "acceptance_role_id": None,
            "rules_channel_id": None,
            "acceptance_prompt_enabled": False
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
            {
                "title": "Rule 1: Be respectful to everyone.",
                "description": (
                    "**1.1** Treat all members with kindness and consideration.\n"
                    "Personal attacks, harassment, and bullying will not be tolerated.\n"
                    "Examples:\n"
                    "- Name-calling or using derogatory terms.\n"
                    "- Sending threatening messages.\n"
                    "- Mocking someone's personal attributes."
                )
            },
            {
                "title": "Rule 2: No spamming or flooding the chat.",
                "description": (
                    "**2.1** Avoid sending repetitive messages, excessive emojis, or large blocks of text.\n"
                    "Examples:\n"
                    "- Posting the same message repeatedly in a short period.\n"
                    "- Using an excessive number of emojis in a single message.\n"
                    "- Sending large blocks of text that disrupt the conversation."
                )
            },
            {
                "title": "Rule 3: No hate speech or offensive language.",
                "description": (
                    "**3.1** This includes any form of discrimination, racism, sexism, homophobia, or any other form of hate speech.\n"
                    "Examples:\n"
                    "- Using racial slurs or derogatory language.\n"
                    "- Making sexist jokes or comments.\n"
                    "- Sharing homophobic or transphobic content."
                )
            },
            {
                "title": "Rule 4: Keep conversations in the appropriate channels.",
                "description": (
                    "**4.1** Use the designated channels for specific topics to keep discussions organized and relevant.\n"
                    "Examples:\n"
                    "- Posting memes in a serious discussion channel.\n"
                    "- Asking for tech support in a general chat.\n"
                    "- Discussing off-topic subjects in a focused channel."
                )
            },
            {
                "title": "Rule 5: Follow the Discord Community Guidelines.",
                "description": (
                    "**5.1** Ensure that your behavior and content comply with Discord's official guidelines.\n"
                    "Link: [Discord Guidelines](https://discord.com/guidelines)\n"
                    "Examples:\n"
                    "- Sharing content that violates Discord's terms.\n"
                    "- Engaging in activities that Discord prohibits.\n"
                    "- Ignoring warnings about guideline violations."
                )
            },
            {
                "title": "Rule 6: Listen to the moderators and admins.",
                "description": (
                    "**6.1** They are here to help maintain a safe and enjoyable environment.\n"
                    "Examples:\n"
                    "- Ignoring direct instructions from moderators.\n"
                    "- Arguing with staff decisions publicly.\n"
                    "- Disrespecting staff members in any form."
                )
            },
            {
                "title": "Rule 7: Do not share dangerous or malicious content.",
                "description": (
                    "**7.1** This includes links to phishing sites, malware, or any other harmful material.\n"
                    "Examples:\n"
                    "- Posting links to suspicious websites.\n"
                    "- Sharing files that contain malware.\n"
                    "- Encouraging others to visit harmful sites."
                )
            },
            {
                "title": "Rule 8: Do not share personal information.",
                "description": (
                    "**8.1** Protect your privacy and the privacy of others by not sharing personal details.\n"
                    "Examples:\n"
                    "- Posting your or others' addresses or phone numbers.\n"
                    "- Sharing private conversations without consent.\n"
                    "- Revealing sensitive personal information."
                )
            },
            {
                "title": "Rule 9: Use appropriate usernames and avatars.",
                "description": (
                    "**9.1** Usernames and avatars should not be offensive, inappropriate, or disruptive.\n"
                    "Examples:\n"
                    "- Using explicit images as avatars.\n"
                    "- Choosing usernames with offensive language.\n"
                    "- Changing usernames to impersonate others."
                )
            },
            {
                "title": "Rule 10: No self-promotion or advertising.",
                "description": (
                    "**10.1** Do not promote your own content, services, or servers without permission.\n"
                    "Examples:\n"
                    "- Posting links to your YouTube channel without approval.\n"
                    "- Advertising your business in chat.\n"
                    "- Inviting members to other servers without consent."
                )
            },
            {
                "title": "Rule 11: No excessive shitposting.",
                "description": (
                    "**11.1** Keep the content meaningful and avoid posting low-effort or irrelevant content excessively.\n"
                    "Examples:\n"
                    "- Posting random memes repeatedly.\n"
                    "- Sharing irrelevant jokes in serious discussions.\n"
                    "- Flooding channels with low-effort content."
                )
            },
            {
                "title": "Rule 12: Staff have the final decision for all moderative actions.",
                "description": (
                    "**12.1** Even if an action is not in clear violation of a rule, staff decisions are to be respected and followed.\n"
                    "Examples:\n"
                    "- Publicly disputing a moderator's decision.\n"
                    "- Attempting to bypass a staff ruling.\n"
                    "- Encouraging others to challenge staff authority."
                )
            },
            {
                "title": "Rule 13: No illegal activities.",
                "description": (
                    "**13.1** Engaging in or promoting illegal activities is strictly prohibited.\n"
                    "Examples:\n"
                    "- Sharing pirated software or media.\n"
                    "- Discussing illegal drug use.\n"
                    "- Planning or promoting illegal activities."
                )
            },
            {
                "title": "Rule 14: Respect privacy and confidentiality.",
                "description": (
                    "**14.1** Do not share private or confidential information without consent.\n"
                    "Examples:\n"
                    "- Leaking private messages or server information.\n"
                    "- Sharing screenshots of private conversations.\n"
                    "- Discussing confidential matters in public channels."
                )
            }
        ]

        for rule in rules:
            embed = discord.Embed(title=rule["title"], description=rule["description"], color=0xfffffe)
            await channel.send(embed=embed)
            await asyncio.sleep(2)

        # Check if acceptance prompt is enabled
        acceptance_prompt_enabled = await self.config.guild(ctx.guild).acceptance_prompt_enabled()
        if acceptance_prompt_enabled:
            await self.send_accept_message(ctx)

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

    @rules_group.command(name='toggleacceptprompt')
    @commands.has_permissions(administrator=True)
    async def toggle_acceptance_prompt(self, ctx):
        """Toggle the acceptance prompt on or off."""
        current_state = await self.config.guild(ctx.guild).acceptance_prompt_enabled()
        new_state = not current_state
        await self.config.guild(ctx.guild).acceptance_prompt_enabled.set(new_state)
        state_str = "enabled" if new_state else "disabled"
        await ctx.send(f"Acceptance prompt has been {state_str}.")

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

