from .phantoncleanup import PhantomCleanup

async def setup(bot):
    cog = PhantomCleanup(bot)
    await bot.add_cog(cog)