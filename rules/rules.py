import discord
from discord.ext import commands

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sendrules')
    async def send_rules(self, ctx):
        rules = [
            "Welcome to the server! Please adhere to the following rules:",
            "1. Be respectful to everyone.",
            "2. No spamming or flooding the chat.",
            "3. No hate speech or offensive language.",
            "4. Keep conversations in the appropriate channels.",
            "5. Follow the Discord Community Guidelines.",
            "6. Listen to the moderators and admins.",
            "7. Have fun and enjoy your stay!"
        ]
        for rule in rules:
            embed = discord.Embed(description=rule, color=0xfffffe)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RulesCog(bot))
