from .phantoncleanup import PhantomCleanup

async def setup(bot: Red):
    cog = PhantomCleanup(bot)
    await bot.add_cog(cog)