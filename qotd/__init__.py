from .qotd import QotD

async def setup(bot):
    cog = QotD(bot)
    await bot.add_cog(cog)

