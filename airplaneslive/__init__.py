from redbot.core.bot import Red

from .airplaneslive import Airplaneslive

async def setup(bot: Red):
    await bot.add_cog(Airplaneslive(bot))