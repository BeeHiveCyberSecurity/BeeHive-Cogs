import discord
from redbot.core import commands, Config
import os
import asyncio
import wave
import pyaudio  # Use PyAudio instead of sounddevice
import aiohttp  # Ensure aiohttp is imported

class OnTheRecord(commands.Cog):
    """A cog to record and transcribe voice channels."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(recordings={})
        self.voice_clients = {}
        self.recording_tasks = {}

    @commands.command(name="on_the_record")
    async def start_recording(self, ctx):
        """Join the voice channel and start recording."""
        if ctx.author.voice is None:
            await ctx.send("You are not connected to a voice channel.")
            return

        channel = ctx.author.voice.channel
        if ctx.guild.id in self.voice_clients:
            await ctx.send("Already recording in this server.")
            return

        try:
            voice_client = await channel.connect()
        except discord.ClientException as e:
            await ctx.send(f"Failed to connect to the voice channel: {str(e)}")
            return

        self.voice_clients[ctx.guild.id] = voice_client
        await ctx.send(f"Joined {channel.name} and started recording.")

        # Start recording in a separate task
        self.recording_tasks[ctx.guild.id] = self.bot.loop.create_task(self.record_audio(ctx.guild.id))

    async def record_audio(self, guild_id):
        """Record audio from the voice channel."""
        voice_client = self.voice_clients[guild_id]
        samplerate = 44100
        channels = 2
        frames = []

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        def callback(in_data, frame_count, time_info, status):
            frames.append(in_data)
            return (in_data, pyaudio.paContinue)

        try:
            stream = p.open(format=pyaudio.paInt16,
                            channels=channels,
                            rate=samplerate,
                            input=True,
                            stream_callback=callback)

            stream.start_stream()

            while guild_id in self.voice_clients:
                await asyncio.sleep(0.1)  # Sleep to allow other tasks to run

            stream.stop_stream()
            stream.close()
        finally:
            p.terminate()
            # Save the recording
            file_path = f"data/ontherecord/{guild_id}_recording.wav"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(samplerate)
                wf.writeframes(b''.join(frames))

            # Update the recordings list in the config
            async with self.config.guild_from_id(guild_id).recordings() as recordings:
                recordings[file_path] = {"name": f"{guild_id}_recording.wav"}

    @commands.command(name="end_recording")
    async def end_recording(self, ctx):
        """End the recording and save it."""
        if ctx.guild.id not in self.voice_clients:
            await ctx.send("Not currently recording in this server.")
            return

        voice_client = self.voice_clients.pop(ctx.guild.id)
        await voice_client.disconnect()

        # Cancel the recording task
        if ctx.guild.id in self.recording_tasks:
            self.recording_tasks[ctx.guild.id].cancel()
            del self.recording_tasks[ctx.guild.id]

        await ctx.send("Recording ended and saved.")

    @commands.command(name="list_recordings")
    async def list_recordings(self, ctx):
        """List all recordings for the server."""
        recordings = await self.config.guild(ctx.guild).recordings()
        if not recordings:
            await ctx.send("No recordings found for this server.")
            return

        recording_list = "\n".join([f"- {info['name']}" for info in recordings.values()])
        await ctx.send(f"Recordings for this server:\n{recording_list}")

    @commands.command(name="transcribe")
    async def transcribe_recording(self, ctx, recording_name: str):
        """Choose a recording to process by sending it to OpenAI to transcribe."""
        file_path = f"data/ontherecord/{recording_name}.wav"
        if not os.path.exists(file_path):
            await ctx.send("Recording not found.")
            return

        await ctx.send(f"Transcribing {recording_name}...")

        # Actual transcription logic
        try:
            openai_api_key = await self.bot.get_shared_api_tokens("openai")
            api_key = openai_api_key.get("api_key")
            if not api_key:
                await ctx.send("OpenAI API key is not configured.")
                return

            with open(file_path, 'rb') as audio_file:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                files = {
                    'file': (recording_name, audio_file, 'audio/wav')
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post('https://api.openai.com/v1/audio/transcriptions', headers=headers, data=files) as response:
                        if response.status == 200:
                            transcription_data = await response.json()
                            transcription_text = transcription_data.get('text', 'No transcription available.')
                            await ctx.send(f"Transcription of {recording_name} completed: {transcription_text}")
                        else:
                            await ctx.send(f"Failed to transcribe {recording_name}. Error: {response.status}")
        except Exception as e:
            await ctx.send(f"An error occurred during transcription: {str(e)}")

