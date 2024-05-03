from redbot.core.bot import Red
from .stripeverify import StripeVerify


async def setup(bot: Red):
    cog = StripeVerify(bot)
    bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data."
