from .omni import Omni

async def setup(bot):
    await bot.add_cog(Omni(bot))
