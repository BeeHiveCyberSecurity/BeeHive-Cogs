from .noinfo import NoInfo

async def setup(bot):
    await bot.add_cog(NoInfo(bot))

