from redbot.core.bot import Red

from .airplaneslive import AirplanesLive

async def setup(bot: Red):
    await bot.add_cog(AirplanesLive(bot))
