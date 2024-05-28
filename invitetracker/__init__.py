from redbot.core.bot import Red  # type: ignore

from .invitetracker import InviteTracker

async def setup(bot: Red):
    bot.add_cog(InviteTracker(bot))
