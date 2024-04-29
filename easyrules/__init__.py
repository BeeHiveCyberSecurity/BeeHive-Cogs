from redbot.core.bot import Red

from .easyrules import EasyRules


async def setup(bot: Red):
    cog = EasyRules(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data."
