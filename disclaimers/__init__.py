from redbot.core.bot import Red

from .disclaimers import Disclaimers

async def setup(bot: Red):
    await bot.add_cog(Disclaimers(bot))

__red_end_user_data_statement__ = "This cog stores flags on a user about their profession."
