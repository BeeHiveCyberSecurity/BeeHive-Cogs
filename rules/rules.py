import discord
from redbot.core import commands
import asyncio  # Ensure asyncio is imported

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sendrules')
    async def send_rules(self, ctx):
        rules = [
            "### Be respectful to everyone.\n> Treat all members with kindness and consideration. Personal attacks, harassment, and bullying will not be tolerated.",
            "### No spamming or flooding the chat.\n> Avoid sending repetitive messages, excessive emojis, or large blocks of text that disrupt the flow of conversation.",
            "### No hate speech or offensive language.\n> This includes any form of discrimination, racism, sexism, homophobia, or any other form of hate speech.",
            "### Keep conversations in the appropriate channels.\n> Use the designated channels for specific topics to keep discussions organized and relevant.",
            "### Follow the Discord Community Guidelines.\n> Ensure that your behavior and content comply with Discord's official guidelines, which can be found at https://discord.com/guidelines.",
            "### Listen to the moderators and admins.\n> They are here to help maintain a safe and enjoyable environment. Follow their instructions and respect their decisions.",
            "### Do not share dangerous or malicious content.\n> This includes links to phishing sites, malware, or any other harmful material.",
            "### Do not share personal information.\n> Protect your privacy and the privacy of others by not sharing personal details such as addresses, phone numbers, or any other sensitive information.",
            "### Staff have the final decision for all moderative actions.\n> Even if an action is not in clear violation of a rule, staff decisions are to be respected and followed.",
            "### Use appropriate usernames and avatars.\n> Usernames and avatars should not be offensive, inappropriate, or disruptive to the community.",
            "### No self-promotion or advertising.\n> Do not promote your own content, services, or servers without permission from the moderators."
        ]
        for rule in rules:
            embed = discord.Embed(description=rule, color=0xfffffe)
            await ctx.send(embed=embed)
            await asyncio.sleep(2)  # Add a delay of 2 seconds between sending each rule

