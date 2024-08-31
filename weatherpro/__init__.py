from .weatherpro import Weather

async def setup(bot):
    await bot.add_cog(Weather(bot))
