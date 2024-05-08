from redbot.core.bot import Red

from .reviews import ReviewsCog  # Corrected import to match the class name in reviews.py


async def setup(bot: Red):
    cog = ReviewsCog(bot)  # Updated to instantiate the correct class
    bot.add_cog(cog)  # Removed await since add_cog is not an async function

__red_end_user_data_statement__ = "This cog does not store any user data."

