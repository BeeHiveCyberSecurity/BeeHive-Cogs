from redbot.core import commands
import discord

class FileInfo(commands.Cog):
    """A cog to display debug information about files shared in a channel."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if the message contains attachments
        if message.attachments:
            for attachment in message.attachments:
                embed = discord.Embed(title="File Information", color=discord.Color.blue())
                embed.add_field(name="File Name", value=attachment.filename, inline=False)
                embed.add_field(name="File Size", value=f"{attachment.size / 1024:.2f} KB", inline=False)
                embed.add_field(name="File Type", value=attachment.content_type, inline=False)
                embed.add_field(name="URL", value=attachment.url, inline=False)
                await message.channel.send(embed=embed)
