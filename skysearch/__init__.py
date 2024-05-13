from redbot.core.bot import Red

from .skysearch import Skysearch

async def setup(bot: Red):
    cog = Skysearch(bot)
    await bot.add_cog(cog)