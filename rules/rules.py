import discord
from redbot.core import commands, Config
import asyncio

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {"acceptance_role_id": None}
        self.config.register_guild(**default_guild)

    @commands.admin_or_permissions()
    @commands.command(name='sendrules')
    async def send_rules(self, ctx):
        rules = [
            "### Rule 1: Be respectful to everyone.\n> 1.1 Treat all members with kindness and consideration. Personal attacks, harassment, and bullying will not be tolerated.",
            "### Rule 2: No spamming or flooding the chat.\n> 2.1 Avoid sending repetitive messages, excessive emojis, or large blocks of text that disrupt the flow of conversation.",
            "### Rule 3: No hate speech or offensive language.\n> 3.1 This includes any form of discrimination, racism, sexism, homophobia, or any other form of hate speech.",
            "### Rule 4: Keep conversations in the appropriate channels.\n> 4.1 Use the designated channels for specific topics to keep discussions organized and relevant.",
            "### Rule 5: Follow the Discord Community Guidelines.\n> 5.1 Ensure that your behavior and content comply with Discord's official guidelines, which can be found at https://discord.com/guidelines.",
            "### Rule 6: Listen to the moderators and admins.\n> 6.1 They are here to help maintain a safe and enjoyable environment. Follow their instructions and respect their decisions.",
            "### Rule 7: Do not share dangerous or malicious content.\n> 7.1 This includes links to phishing sites, malware, or any other harmful material.",
            "### Rule 8: Do not share personal information.\n> 8.1 Protect your privacy and the privacy of others by not sharing personal details such as addresses, phone numbers, or any other sensitive information.",
            "### Rule 9: Use appropriate usernames and avatars.\n> 9.1 Usernames and avatars should not be offensive, inappropriate, or disruptive to the community.",
            "### Rule 10: No self-promotion or advertising.\n> 10.1 Do not promote your own content, services, or servers without permission from the moderators.",
            "### Rule 11: No excessive shitposting.\n> 11.1 Keep the content meaningful and avoid posting low-effort or irrelevant content excessively.",
            "### Rule 12: Staff have the final decision for all moderative actions.\n> 12.1 Even if an action is not in clear violation of a rule, staff decisions are to be respected and followed."
        ]
        for rule in rules:
            embed = discord.Embed(description=rule, color=0xfffffe)
            await ctx.send(embed=embed)
            await asyncio.sleep(2)

    @commands.command(name='setacceptancerole')
    @commands.has_permissions(manage_roles=True)
    async def set_acceptance_role(self, ctx, role: discord.Role):
        """Set the role to be given when a user accepts the rules."""
        await self.config.guild(ctx.guild).acceptance_role_id.set(role.id)
        await ctx.send(f"Acceptance role set to: {role.name}")

    @commands.command(name='sendacceptmsg')
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
                reaction, user = await self.bot.wait_for('reaction_add', check=check)
                role = ctx.guild.get_role(acceptance_role_id)
                if role:
                    await user.add_roles(role)
            except asyncio.TimeoutError:
                break

