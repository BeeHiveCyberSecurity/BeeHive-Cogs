from redbot.core.bot import Red

from .urlscan import URLScan


async def setup(bot: Red):
    cog = URLScan(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data. URLs scanned with URLScan are shown publicly to other users."
