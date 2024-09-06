from .noinfo import NoInfo

async def setup(bot):
    bot.add_cog(NoInfo(bot))

