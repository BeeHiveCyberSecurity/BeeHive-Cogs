from redbot.core.bot import Red #type: ignore

from .skysearch import Skysearch

async def setup(bot: Red):
    cog = Skysearch(bot)
    await bot.add_cog(cog)