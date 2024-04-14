from redbot.core.bot import Red

from .virustotal import VirusTotal


async def setup(bot: Red):
    cog = Malcore(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "The VirusTotal cog by BeeHive does not store any user data. VirusTotal stores submitted file information subject to their own Terms of Service and Privacy Policy."
