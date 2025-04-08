from .ontherecord import OnTheRecord

async def setup(bot):
    cog = OnTheRecord(bot)
    await bot.add_cog(cog)
