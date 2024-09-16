from .abuseipdb import AbuseIPDB

async def setup(bot):
    cog = AbuseIPDB(bot)
    await bot.add_cog(cog)

