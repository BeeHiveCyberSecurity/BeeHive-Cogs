from redbot.core.bot import Red

from .virustotal import VirusTotal


async def setup(bot: Red):
    cog = VirusTotal(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any end user data."
