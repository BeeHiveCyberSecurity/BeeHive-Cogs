from redbot.core.bot import Red

from .products import Products


async def setup(bot: Red):
    global old_licenseinfo
    old_licenseinfo = bot.get_command("licenseinfo")
    if old_licenseinfo:
        bot.remove_command(old_licenseinfo.name)
    cog = Products(bot)
    await bot.add_cog(cog)


__red_end_user_data_statement__ = "This cog does not store any user data."