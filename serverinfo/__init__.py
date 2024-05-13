from redbot.core.bot import Red #type: ignore

from .serverinfo import ServerInfoCog


async def setup(bot: Red):
    cog = ServerInfoCog(bot)
    await bot.add_cog(cog)

__red_end_user_data_statement__ = "This cog does not store any user data."


