from redbot.core.bot import Red

from .reviews import Reviews


async def setup(bot: Red):
    cog = Reviews(bot)
    await cog.initialize()
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data."
