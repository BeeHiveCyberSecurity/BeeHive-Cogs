from .shazam import ShazamCog

async def setup(bot):
    cog = ShazamCog(bot)
    await bot.add_cog(cog)