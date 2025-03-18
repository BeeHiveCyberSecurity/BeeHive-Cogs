from redbot.core.bot import Red

from .staffmanager import StaffManager

async def setup(bot: Red):
    cog = StaffManager(bot)
    await bot.add_cog(cog)
