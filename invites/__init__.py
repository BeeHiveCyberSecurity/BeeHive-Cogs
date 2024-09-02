from redbot.core.bot import Red  # type: ignore

from .invites import InviteTracker

async def setup(bot: Red):
    await bot.add_cog(InviteTracker(bot))
