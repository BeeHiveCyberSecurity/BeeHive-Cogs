from .tiktoklive import TikTokLiveCog

async def setup(bot):
    await bot.add_cog(TikTokLiveCog(bot))

