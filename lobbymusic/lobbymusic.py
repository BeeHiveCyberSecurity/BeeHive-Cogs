from redbot.core import commands
import discord
import os
import random

class LobbyMusic(commands.Cog):
    """A cog to play folders of pre-selected music."""

    def __init__(self, bot):
        self.bot = bot
        self.music_folder = "./music/"  # Set the path to your music folder

    @commands.group()
    async def lobbymusic(self, ctx):
        """Group of commands to manage lobby music."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand: play or stop.")

    @lobbymusic.command()
    async def play(self, ctx):
        """Play a random music file from the pre-selected folder."""
        if not os.path.exists(self.music_folder):
            await ctx.send("Music folder not found.")
            return

        music_files = [f for f in os.listdir(self.music_folder) if f.endswith(('.mp3', '.wav'))]
        if not music_files:
            await ctx.send("No music files found in the folder.")
            return

        selected_music = random.choice(music_files)
        music_path = os.path.join(self.music_folder, selected_music)

        # Assuming you have a method to connect to a voice channel and play music
        voice_channel = ctx.author.voice.channel
        if voice_channel is not None:
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(music_path), after=lambda e: print(f"Finished playing: {e}"))
            await ctx.send(f"Now playing: {selected_music}")
        else:
            await ctx.send("You need to be in a voice channel to play music.")

    @lobbymusic.command()
    async def stop(self, ctx):
        """Stop the currently playing music."""
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            await ctx.send("Music stopped.")
        else:
            await ctx.send("No music is currently playing.")
