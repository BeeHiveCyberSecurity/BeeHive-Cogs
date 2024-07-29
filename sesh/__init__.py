from .sesh import Sesh

async def setup(bot):
    await bot.add_cog(Sesh(bot))

__red_end_user_data_statement__ = "This cog does not store any user data."
