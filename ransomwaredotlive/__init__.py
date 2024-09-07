from .ransomwaredotlive import RansomwareDotLive

async def setup(bot):
    cog = RansomwareDotLive(bot)
    await bot.add_cog(cog)
