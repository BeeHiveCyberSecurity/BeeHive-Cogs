from .meetings import Meetings

async def setup(bot):
    cog = Meetings(bot)
    await bot.add_cog(cog)
