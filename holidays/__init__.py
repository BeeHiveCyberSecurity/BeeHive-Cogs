from .holidays import Holidays

async def setup(bot):
    cog = Holidays(bot)
    bot.add_cog(cog)
