from .lobbymusic import LobbyMusic

async def setup(bot):
    cog = LobbyMusic(bot)
    await bot.add_cog(cog)
