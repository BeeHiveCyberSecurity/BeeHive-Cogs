from .holidays import Holidays

async def setup(bot):
    cog = Holidays(bot)
    await bot.add_cog(cog)
