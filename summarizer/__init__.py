from .summarizer import ChatSummary

async def setup(bot):
    cog = ChatSummary(bot)
    await bot.add_cog(cog)
