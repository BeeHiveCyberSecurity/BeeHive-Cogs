from .rules import RulesCog
from redbot.core import commands

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(RulesCog(bot))

