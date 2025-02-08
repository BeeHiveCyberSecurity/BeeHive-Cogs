from .phantomclean import PhantomClean

async def setup(bot):
    cog = PhantomClean(bot)
    await bot.add_cog(cog)