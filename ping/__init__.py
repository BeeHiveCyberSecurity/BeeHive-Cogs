from .ping import Ping

async def setup(bot):
    await bot.add_cog(Ping(bot))

__red_end_user_data_statement__ = "This cog does not store any user data."
