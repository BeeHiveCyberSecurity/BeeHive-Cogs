from .offers import Offers

def setup(bot):
    cog = Offers(bot)
    bot.add_cog(cog)

