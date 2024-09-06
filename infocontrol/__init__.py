from .infocontrol import InfoControl

async def setup(bot):
    await bot.add_cog(InfoControl(bot))

