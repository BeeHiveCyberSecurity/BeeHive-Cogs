from redbot.core.bot import Red  # type: ignore

from .invites import Invites

async def setup(bot: Red):
    await bot.add_cog(Invites(bot))
