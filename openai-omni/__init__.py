from .openai_omni import OpenAIModerationCog

async def setup(bot):
    await bot.add_cog(OpenAIModerationCog(bot))
