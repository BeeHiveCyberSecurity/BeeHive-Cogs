from .triage import Triage
from triage import Client

async def setup(bot):
    cog = Triage(bot)
    await bot.add_cog(cog)
