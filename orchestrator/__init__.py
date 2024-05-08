from .orchestrator import Orchestrator
from redbot.core.utils import get_end_user_data_statement

__red_end_user_data_statement__ = "This cog does not store any End User Data."

async def setup(bot):
    await bot.add_cog(Orchestrator(bot))
