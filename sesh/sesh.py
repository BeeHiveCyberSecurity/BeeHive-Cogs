from redbot.core import commands, Config
import discord
import datetime
import asyncio  # Ensure asyncio is imported
import uuid  # Import uuid for generating unique session IDs
import speech_recognition as sr  # Import speech recognition library

class Sesh(commands.Cog):
    """Coordinate smoking sessions with your friends."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "sessions": [],
            "mention_role": None  # Add default for mention role
        }
        self.config.register_guild(**default_guild)
        
    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def sesh(self, ctx):
        """Group command for managing smoking sessions."""
        sessions = await self.config.guild(ctx.guild).sessions()
        if sessions:
            current_session = sessions[-1]  # Assuming the last session is the active one
            embed = discord.Embed(
                title="We're blazing up!",
                description=f"**Description:** {current_session['description']}\n"
                            f"**Ends at:** {current_session['end_time']}\n"
                            f"**Participants:** {len(current_session['participants'])}",
                color=discord.Color.green()
            )
            if 'voice_channel_id' in current_session:
                voice_channel = ctx.guild.get_channel(current_session['voice_channel_id'])
                if voice_channel:
                    embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({voice_channel.jump_url})", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send_help(ctx.command)

    @commands.guild_only()
    @sesh.command()
    async def setrole(self, ctx, role: discord.Role):
        """Set a role to be mentioned when a sesh is announced or starts."""
        await self.config.guild(ctx.guild).mention_role.set(role.id)
        await ctx.send(f"The role {role.name} will now be mentioned for sesh announcements.")

    @commands.guild_only()
    @sesh.command()
    async def start(self, ctx, duration: str, *, description: str):
        """Start a new smoking session.
        
        Duration can be in minutes or in the format 'in X minutes'.
        """
        mention_role_id = await self.config.guild(ctx.guild).mention_role()
        mention_role = ctx.guild.get_role(mention_role_id) if mention_role_id else None

        async def update_channel_status(voice_channel, session):
            while True:
                current_time = datetime.datetime.utcnow()
                remaining_time = session["end_time"] - current_time
                if remaining_time.total_seconds() <= 0:
                    break

                participant_types = [p["type"] for p in session["participants"]]
                most_popular_type = max(set(participant_types), key=participant_types.count)
                participant_count = len(session["participants"])

                new_name = f"Sesh-{session['id']} | Ends in {remaining_time.seconds // 60}m | {most_popular_type} | {participant_count} participants"
                await voice_channel.edit(name=new_name)
                await asyncio.sleep(60)  # Update every minute

        async def listen_for_cheers(voice_channel, text_channel):
            recognizer = sr.Recognizer()
            mic = sr.Microphone()

            while True:
                if not voice_channel.members:
                    break

                with mic as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source)

                try:
                    speech_text = recognizer.recognize_google(audio)
                    if "cheers" in speech_text.lower():
                        await text_channel.send("Cheers! It's time to take a hit!")
                except sr.UnknownValueError:
                    pass  # Ignore unrecognized speech
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")

                await asyncio.sleep(5)  # Prevent spamming, wait a bit before listening again

        if duration.startswith("in "):
            try:
                delay = int(duration.split(" ")[1])
                await ctx.send(f"Session scheduled to start in {delay} minutes. Please select the session duration from the dropdown below.")
                
                options = [
                    discord.SelectOption(label="15 minutes", value="15"),
                    discord.SelectOption(label="30 minutes", value="30"),
                    discord.SelectOption(label="45 minutes", value="45"),
                    discord.SelectOption(label="1 hour", value="60")
                ]
                
                select = discord.ui.Select(placeholder="Select session duration", options=options)
                
                async def select_callback(interaction):
                    session_duration = int(interaction.data['values'][0])
                    session_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=delay)
                    session_end_time = session_time + datetime.timedelta(minutes=session_duration)
                    
                    session_id = str(uuid.uuid4())  # Generate a unique session ID
                    session = {
                        "id": session_id,
                        "time": session_time,
                        "end_time": session_end_time,
                        "description": description,
                        "creator": ctx.author.id,
                        "participants": [{"id": ctx.author.id, "type": "N/A", "strain": "N/A"}]
                    }

                    async with self.config.guild(ctx.guild).sessions() as sessions:
                        sessions.append(session)

                    embed = discord.Embed(
                        title="Smoking Session Started",
                        description=f"A new smoking session has started and will last for {session_duration} minutes.\n\n**Description:** {description}\n**Session ID:** {session_id}",
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"Started by {ctx.author.display_name}")

                    if ctx.author.voice:
                        voice_channel = ctx.author.voice.channel
                        invite = await voice_channel.create_invite(max_age=session_duration * 60)
                        embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)
                    else:
                        # Create a new voice channel named after the session ID
                        voice_channel = await ctx.guild.create_voice_channel(name=f"Sesh-{session_id}")
                        # Make the bot join the new voice channel
                        await voice_channel.connect()
                        invite = await voice_channel.create_invite(max_age=session_duration * 60)
                        embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)

                    if mention_role:
                        await ctx.send(f"{mention_role.mention}", embed=embed)
                    else:
                        await ctx.send(embed=embed)

                    self.bot.loop.create_task(update_channel_status(voice_channel, session))
                    self.bot.loop.create_task(listen_for_cheers(voice_channel, ctx.channel))
                
                select.callback = select_callback
                view = discord.ui.View()
                view.add_item(select)
                await ctx.send("Select the session duration:", view=view)
                
            except (ValueError, IndexError):
                await ctx.send("Invalid format. Please use 'in X minutes' or just provide the duration in minutes.")
                return
        else:
            try:
                session_duration = int(duration)
                session_time = datetime.datetime.utcnow()
                session_end_time = session_time + datetime.timedelta(minutes=session_duration)
                
                session_id = str(uuid.uuid4())  # Generate a unique session ID
                session = {
                    "id": session_id,
                    "time": session_time,
                    "end_time": session_end_time,
                    "description": description,
                    "creator": ctx.author.id,
                    "participants": [{"id": ctx.author.id, "type": "N/A", "strain": "N/A"}]
                }

                async with self.config.guild(ctx.guild).sessions() as sessions:
                    sessions.append(session)

                embed = discord.Embed(
                    title="It's sesh time!",
                    description=f"A new smoking session has started and will last for {session_duration} minutes.\n\n**Description:** {description}\n**Session ID:** {session_id}",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Started by {ctx.author.display_name}")

                if ctx.author.voice:
                    voice_channel = ctx.author.voice.channel
                    invite = await voice_channel.create_invite(max_age=session_duration * 60)
                    embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)
                else:
                    # Create a new voice channel named after the session ID
                    voice_channel = await ctx.guild.create_voice_channel(name=f"Sesh-{session_id}")
                    # Make the bot join the new voice channel
                    await voice_channel.connect()
                    invite = await voice_channel.create_invite(max_age=session_duration * 60)
                    embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)

                if mention_role:
                    await ctx.send(f"{mention_role.mention}", embed=embed)
                else:
                    await ctx.send(embed=embed)

                self.bot.loop.create_task(update_channel_status(voice_channel, session))
                self.bot.loop.create_task(listen_for_cheers(voice_channel, ctx.channel))
                
            except ValueError:
                await ctx.send("Invalid duration. Please provide the duration in minutes.")
                return

    @commands.guild_only()
    @sesh.command()
    async def join(self, ctx):
        """Join the currently active smoking session."""
        async with self.config.guild(ctx.guild).sessions() as sessions:
            current_time = datetime.datetime.utcnow()
            for session in sessions:
                if session["time"] <= current_time < session["end_time"]:
                    if not any(p["id"] == ctx.author.id for p in session["participants"]):
                        await ctx.send("What type of marijuana are you consuming? (e.g., flower, concentrate, distillate, edibles, etc.)", 
                                       components=[
                                           discord.ui.Button(label="Flower", style=discord.ButtonStyle.primary, custom_id="flower"),
                                           discord.ui.Button(label="Concentrate", style=discord.ButtonStyle.primary, custom_id="concentrate"),
                                           discord.ui.Button(label="Distillate", style=discord.ButtonStyle.primary, custom_id="distillate"),
                                           discord.ui.Button(label="Edibles", style=discord.ButtonStyle.primary, custom_id="edibles")
                                       ])
                        
                        def check_type(interaction):
                            return interaction.user == ctx.author and interaction.message.channel == ctx.channel
                        
                        try:
                            type_interaction = await self.bot.wait_for('interaction', check=check_type, timeout=60.0)
                            marijuana_type = type_interaction.data['custom_id']
                            await type_interaction.response.send_message(f"You selected {marijuana_type}. Now, is it indica, sativa, or a hybrid?", 
                                                                         components=[
                                                                             discord.ui.Button(label="Indica", style=discord.ButtonStyle.primary, custom_id="indica"),
                                                                             discord.ui.Button(label="Sativa", style=discord.ButtonStyle.primary, custom_id="sativa"),
                                                                             discord.ui.Button(label="Hybrid", style=discord.ButtonStyle.primary, custom_id="hybrid")
                                                                         ])
                        except asyncio.TimeoutError:
                            await ctx.send("You took too long to respond. Please try joining the session again.")
                            return
                        
                        try:
                            strain_interaction = await self.bot.wait_for('interaction', check=check_type, timeout=60.0)
                            strain_type = strain_interaction.data['custom_id']
                            await strain_interaction.response.send_message(f"You selected {strain_type}. You have joined the session.")
                        except asyncio.TimeoutError:
                            await ctx.send("You took too long to respond. Please try joining the session again.")
                            return
                        
                        session["participants"].append({
                            "id": ctx.author.id,
                            "type": marijuana_type,
                            "strain": strain_type
                        })
                        await ctx.send(f"You have joined the smoking session at {session['time'].strftime('%H:%M')} with {marijuana_type} ({strain_type}).")
                    else:
                        await ctx.send("You are already in this session.")
                    return
            await ctx.send("No active session found at this time.")

    @commands.guild_only()
    @sesh.command()
    async def leave(self, ctx):
        """Leave the current smoking session."""
        async with self.config.guild(ctx.guild).sessions() as sessions:
            for session in sessions:
                for participant in session["participants"]:
                    if participant["id"] == ctx.author.id:
                        session["participants"].remove(participant)
                        await ctx.send(f"You have left the smoking session at {session['time'].strftime('%H:%M')}.")
                        return
            await ctx.send("You are not currently in any smoking session.")

    @commands.guild_only()
    @sesh.command()
    async def list(self, ctx):
        """List all upcoming smoking sessions."""
        sessions = await self.config.guild(ctx.guild).sessions()
        if not sessions:
            await ctx.send("No upcoming smoking sessions.")
            return

        embed = discord.Embed(title="Upcoming Smoking Sessions", color=discord.Color.green())
        for session in sessions:
            creator = self.bot.get_user(session["creator"])
            participants = [self.bot.get_user(p["id"]) for p in session["participants"]]
            participant_details = ", ".join([f"{p.name} ({p['type']}, {p['strain']})" for p in session["participants"] if p])
            embed.add_field(
                name=f"Session ID: {session['id']}",
                value=f"Time: {session['time'].strftime('%H:%M')}\nDescription: {session['description']}\nCreator: {creator.name if creator else 'Unknown'}\nParticipants: {participant_details}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.guild_only()
    @sesh.command()
    async def cancel(self, ctx, session_id: str):
        """Cancel a smoking session you created.
        
        Provide the session ID to cancel the session.
        """
        async with self.config.guild(ctx.guild).sessions() as sessions:
            for session in sessions:
                if session["id"] == session_id and session["creator"] == ctx.author.id:
                    sessions.remove(session)
                    await ctx.send(f"Smoking session with ID {session_id} has been cancelled.")
                    return
            await ctx.send("No session found with that ID or you are not the creator of the session.")

async def setup(bot):
    await bot.add_cog(Sesh(bot))
