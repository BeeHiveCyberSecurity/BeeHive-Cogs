from .fileinfo import FileInfo

async def setup(bot):
    cog = FileInfo(bot)
    await bot.add_cog(cog)
