from .vanityguard import VanityGuard

async def setup(bot):
    await bot.add_cog(VanityGuard(bot))
