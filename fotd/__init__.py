from .fotd import Fotd

async def async_setup(bot):
    cog = Fotd(bot)
    await bot.add_cog(cog)

