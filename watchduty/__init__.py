from .watchduty import WatchDuty

async def setup(bot):
    cog = WatchDuty(bot)
    await bot.add_cog(cog)
