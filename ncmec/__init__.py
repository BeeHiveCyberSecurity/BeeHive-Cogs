from .ncmec import MissingKids

async def setup(bot):
    cog = MissingKids(bot)
    await bot.add_cog(cog)
