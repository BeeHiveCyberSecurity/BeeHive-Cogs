from .openbanlist import OpenBanList

async def setup(bot):
    await bot.add_cog(OpenBanList(bot))
