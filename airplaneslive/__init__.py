from redbot.core.bot import Red

from .airplaneslive import Airplaneslive

async def setup(bot: Red):
    cog = Airplaneslive(bot)
    await bot.add_cog(cog)