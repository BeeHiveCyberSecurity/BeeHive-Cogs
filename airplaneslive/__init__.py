from redbot.core.bot import Red

from .airplaneslive import airplaneslive

async def setup(bot: Red):
    await bot.add_cog(AirplanesLive(bot))

async def setup(bot: Red):
    cog = AirplanesLive(bot)
    await cog.initialize()
    await bot.add_cog(cog)