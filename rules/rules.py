import discord
from discord.ext import commands

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sendrules')
    async def send_rules(self, ctx):
        rules = [
            "Be respectful to everyone. Treat all members with kindness and consideration. Personal attacks, harassment, and bullying will not be tolerated.",
            "No spamming or flooding the chat. Avoid sending repetitive messages, excessive emojis, or large blocks of text that disrupt the flow of conversation.",
            "No hate speech or offensive language. This includes any form of discrimination, racism, sexism, homophobia, or any other form of hate speech.",
            "Keep conversations in the appropriate channels. Use the designated channels for specific topics to keep discussions organized and relevant.",
            "Follow the Discord Community Guidelines. Ensure that your behavior and content comply with Discord's official guidelines, which can be found at https://discord.com/guidelines.",
            "Listen to the moderators and admins. They are here to help maintain a safe and enjoyable environment. Follow their instructions and respect their decisions.",
            "Do not share dangerous or malicious content. This includes links to phishing sites, malware, or any other harmful material.",
            "Do not share personal information. Protect your privacy and the privacy of others by not sharing personal details such as addresses, phone numbers, or any other sensitive information.",
            "Have fun and enjoy your stay! Engage with the community, participate in events, and make the most out of your time here.",
            "Staff have the final decision for all moderative actions. Even if an action is not in clear violation of a rule, staff decisions are to be respected and followed."
        ]
        for rule in rules:
            embed = discord.Embed(description=rule, color=0xfffffe)
            await ctx.send(embed=embed)
            await asyncio.sleep(2)  # Add a delay of 1 second between sending each rule

