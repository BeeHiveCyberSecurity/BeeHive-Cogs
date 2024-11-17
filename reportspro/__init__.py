from .reportspro import ReportsPro

async def setup(bot):
    bot.add_cog(ReportsPro(bot))
