from .meetings import Meetings

async def setup(bot):
    cog = Meetings(bot)
    bot.add_cog(cog)
