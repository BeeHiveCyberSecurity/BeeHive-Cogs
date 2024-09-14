from .alertsinua import WarActivity

async def setup(bot):
    await bot.add_cog(WarActivity(bot))
