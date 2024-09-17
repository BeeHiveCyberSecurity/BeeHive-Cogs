from .triage import Triage
from redbot.core.bot import Red

async def setup(bot: Red):
    cog = Triage(bot)
    await bot.add_cog(cog)
