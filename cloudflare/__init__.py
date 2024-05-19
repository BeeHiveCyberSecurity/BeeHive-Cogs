from .cloudflare import Cloudflare

async def setup(bot):
    cog = Cloudflare(bot)
    bot.add_cog(cog)
