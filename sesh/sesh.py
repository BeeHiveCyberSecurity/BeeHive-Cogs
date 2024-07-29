from redbot.core import commands, Config
import discord
import datetime
import asyncio  # Ensure asyncio is imported
import uuid  # Import uuid for generating unique session IDs

class Sesh(commands.Cog):
    """Coordinate smoking sessions with your friends."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "sessions": []
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    async def sesh(self, ctx):
        """Group command for managing smoking sessions."""
        pass

    @sesh.command()
    async def start(self, ctx, duration: str, *, description: str):
        """Start a new smoking session.
        
        Duration can be in minutes or in the format 'in X minutes'.
        """
        if duration.startswith("in "):
            try:
                delay = int(duration.split(" ")[1])
                await ctx.send(f"Session scheduled to start in {delay} minutes. How long should the session last (in minutes)?")
                
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
                
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                    session_duration = int(msg.content)
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to respond. Please try starting the session again.")
                    return
                
                session_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=delay)
                session_end_time = session_time + datetime.timedelta(minutes=session_duration)
            except (ValueError, IndexError):
                await ctx.send("Invalid format. Please use 'in X minutes' or just provide the duration in minutes.")
                return
        else:
            try:
                session_duration = int(duration)
                session_time = datetime.datetime.utcnow()
                session_end_time = session_time + datetime.timedelta(minutes=session_duration)
            except ValueError:
                await ctx.send("Invalid duration. Please provide the duration in minutes.")
                return

        session_id = str(uuid.uuid4())  # Generate a unique session ID
        session = {
            "id": session_id,
            "time": session_time.strftime("%H:%M"),
            "end_time": session_end_time.strftime("%H:%M"),
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

        await ctx.send(embed=embed)

    @sesh.command()
    async def join(self, ctx):
        """Join the currently active smoking session."""
        async with self.config.guild(ctx.guild).sessions() as sessions:
            current_time = datetime.datetime.utcnow().strftime("%H:%M")
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
                        await ctx.send(f"You have joined the smoking session at {session['time']} with {marijuana_type} ({strain_type}).")
                    else:
                        await ctx.send("You are already in this session.")
                    return
            await ctx.send("No active session found at this time.")

    @sesh.command()
    async def leave(self, ctx):
        """Leave the current smoking session."""
        async with self.config.guild(ctx.guild).sessions() as sessions:
            for session in sessions:
                for participant in session["participants"]:
                    if participant["id"] == ctx.author.id:
                        session["participants"].remove(participant)
                        await ctx.send(f"You have left the smoking session at {session['time']}.")
                        return
            await ctx.send("You are not currently in any smoking session.")

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
                value=f"Time: {session['time']}\nDescription: {session['description']}\nCreator: {creator.name if creator else 'Unknown'}\nParticipants: {participant_details}",
                inline=False
            )

        await ctx.send(embed=embed)

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

def setup(bot):
    bot.add_cog(Sesh(bot))
