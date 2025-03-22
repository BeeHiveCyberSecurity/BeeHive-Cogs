from .offers import Offers

async def setup(bot):
    cog = Offers(bot)
    await bot.add_cog(cog)

