from . import triage

async def setup(bot):
    cog = triage.Triage(bot)
    await bot.add_cog(cog)
