from .reportspro import ReportsPro

async def setup(bot):
    cog = ReportsPro(bot)
    bot.add_cog(cog)
