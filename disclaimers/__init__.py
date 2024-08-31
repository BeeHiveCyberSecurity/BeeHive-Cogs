from redbot.core.bot import Red

from .disclaimers import Disclaimers

async def setup(bot: Red):
    cog = Disclaimers(bot)
    await bot.add_cog(cog)

__red_end_user_data_statement__ = "This cog stores flags on a user about their profession."
