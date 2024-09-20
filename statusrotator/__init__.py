from .statusrotator import StatusRotator

async def setup(bot):
    await bot.add_cog(StatusRotator(bot))

