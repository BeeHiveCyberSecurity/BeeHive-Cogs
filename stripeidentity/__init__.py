from redbot.core.bot import Red

from .stripeidentity import StripeIdentity


async def setup(bot: Red):
    cog = StripeIdentity(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data."


