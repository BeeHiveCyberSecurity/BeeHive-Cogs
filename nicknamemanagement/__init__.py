from .nicknamemanagement import NicknameManagement

async def setup(bot):
    cog = NicknameManagement(bot)
    await bot.add_cog(cog)
