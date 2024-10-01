from .fotd import FotD

async def async_setup(bot):
    cog = FotD(bot)
    await bot.add_cog(cog)

