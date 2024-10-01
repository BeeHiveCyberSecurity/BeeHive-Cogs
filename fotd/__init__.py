from .fotd import FotD

async def setup(bot):
    cog = FotD(bot)
    await bot.add_cog(cog)

