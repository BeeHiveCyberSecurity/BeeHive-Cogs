from .triage import Triage

async def setup(bot):
    cog = Triage(bot)
    await bot.add_cog(cog)
