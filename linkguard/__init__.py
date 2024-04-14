from redbot.core.bot import Red

from .linkguard import LinkGuard


async def setup(bot: Red):
    cog = LinkGuard(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any end user data."
