from .v2a import VideoToAudio

async def setup(bot):
    cog = VideoToAudio(bot)
    await bot.add_cog(cog)
