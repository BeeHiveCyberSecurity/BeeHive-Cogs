from redbot.core.bot import Red

from .malcore import Malcore


async def setup(bot: Red):
    cog = Malcore(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data. Samples shared with Malcore are kept public unless the user participating, and their API Key, are enrolled in the Malcore Signature Research Program."
