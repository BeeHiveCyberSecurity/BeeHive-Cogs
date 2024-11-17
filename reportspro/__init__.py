from .reportspro import ReportsPro

async def setup(bot):
    cog = ReportsPro(bot)
    await bot.add_cog(cog)
