from redbot.core.bot import Red  # type: ignore

from .invites import InviteTracker

async def setup(bot: Red):
    cog = InviteTracker(bot)
    await bot.add_cog(cog)
