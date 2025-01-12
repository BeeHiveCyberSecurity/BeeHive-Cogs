from .vanityguard import VanityGuard

async def setup(bot):
    bot.add_cog(VanityGuard(bot))
