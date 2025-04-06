from .openai_transcribe import OpenAITranscribe

async def setup(bot):
    await bot.add_cog(OpenAITranscribe(bot))
