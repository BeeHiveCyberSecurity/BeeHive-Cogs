from .ping import Ping

async def setup(bot):
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    await bot.add_cog(Ping(bot))

__red_end_user_data_statement__ = "This cog does not store any user data."
