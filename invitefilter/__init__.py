from .invitefilter import InviteFilter

async def setup(bot):
    cog = InviteFilter(bot)
    bot.add_cog(cog)
