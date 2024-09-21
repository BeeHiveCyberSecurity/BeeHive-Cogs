from .reviews import ReviewsCog
from redbot.core.bot import Red


async def setup(bot: Red):
    cog = ReviewsCog(bot)
    await bot.add_cog(cog)

__red_end_user_data_statement__ = "This cog does not store any user data."

