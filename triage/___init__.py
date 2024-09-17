from .triage import Triage

async def setup(bot: Red):
    cog = Triage(bot)
    await bot.add_cog(cog)
