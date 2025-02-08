from redbot.core.bot import Red

async def setup(bot: Red):
    bot.add_cog(PhantomCleanup(bot))