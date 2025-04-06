from .transcriber import Transcriber

async def setup(bot):
    cog = Transcriber(bot)
    await bot.add_cog(cog)
