from redbot.core.bot import Red

from .joinmaster import JoinMaster


async def setup(bot: Red):
    cog = JoinMaster(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data. It only facilitates joining servers using OAuth2."
