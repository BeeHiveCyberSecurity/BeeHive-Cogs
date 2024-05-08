import discord
from discord.ext import commands
import aiohttp
import asyncio

class ValkyrieCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.valkyrie_url = "https://valkyrie.comodo.com/api/"
        self.api_key = await self.bot.get_shared_api_tokens("valkyrie")

    @commands.command(name="checkfile")
    async def check_file(self, ctx, *, message: discord.Message = None):
        if not message:
            embed = discord.Embed(description="Please reply to a message with a file to check.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if not message.attachments:
            embed = discord.Embed(description="No files found in the message. Please attach a file.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        for attachment in message.attachments:
            if attachment.size > 8 * 1024 * 1024:  # 8 MB file size limit
                embed = discord.Embed(description=f"The file {attachment.filename} is too large to analyze.", color=discord.Color.red())
                await ctx.send(embed=embed)
                continue

            embed = discord.Embed(description=f"Analyzing {attachment.filename}...", color=discord.Color.blue())
            await ctx.send(embed=embed)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.valkyrie_url,
                    headers={"apikey": self.api_key},
                    data={"file": await attachment.read()}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        result_embed = discord.Embed(title="Analysis Complete", description=f"Result for {attachment.filename}:", color=discord.Color.green())
                        result_embed.add_field(name="Result", value=str(result), inline=False)
                        await ctx.send(embed=result_embed)
                    else:
                        error_embed = discord.Embed(description=f"Failed to analyze {attachment.filename}. Please try again later.", color=discord.Color.red())
                        await ctx.send(embed=error_embed)

def setup(bot):
    bot.add_cog(ValkyrieCog(bot))

