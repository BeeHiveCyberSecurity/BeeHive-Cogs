from redbot.core.bot import Red

from .urlscan import URLScan


async def setup(bot: Red):
    cog = URLScan(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data. Samples shared with URLScan are kept public unless the user participating, and their API Key, are enrolled in the URLScan Signature Research Program."
