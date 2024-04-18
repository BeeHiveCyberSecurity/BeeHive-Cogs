from redbot.core.bot import Red

from .products import Products


async def setup(bot: Red):
    cog = Products(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data."