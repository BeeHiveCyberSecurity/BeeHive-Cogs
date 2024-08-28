from redbot.core import commands, Config #type: ignore
import discord #type: ignore
import datetime
import asyncio
import random
import string

class Sesh(commands.Cog):
    """Coordinate smoking sessions with your friends."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "sessions": [],
            "mention_role": None,  # Add default for mention role
            "announcement_channel": None,  # Add default for announcement channel
            "voice_channel_category": None  # Add default for voice channel category
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
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where sesh announcements will be made."""
        await self.config.guild(ctx.guild).announcement_channel.set(channel.id)
        await ctx.send(f"Sesh announcements will now be made in {channel.mention}.")

    @commands.guild_only()
    @sesh.command()
    async def setcategory(self, ctx, category: discord.CategoryChannel):
        """Set the category where sesh voice channels will be created."""
        await self.config.guild(ctx.guild).voice_channel_category.set(category.id)
        await ctx.send(f"Sesh voice channels will now be created under the category {category.name}.")

    @commands.guild_only()
    @sesh.command()
    async def start(self, ctx):
        """Start a new smoking session using interactive components."""
        mention_role_id = await self.config.guild(ctx.guild).mention_role()
        mention_role = ctx.guild.get_role(mention_role_id) if mention_role_id else None
        announcement_channel_id = await self.config.guild(ctx.guild).announcement_channel()
        announcement_channel = ctx.guild.get_channel(announcement_channel_id) if announcement_channel_id else ctx.channel
        voice_channel_category_id = await self.config.guild(ctx.guild).voice_channel_category()
        voice_channel_category = ctx.guild.get_channel(voice_channel_category_id) if voice_channel_category_id else None

        async def update_channel_status(voice_channel, session):
            while True:
                current_time = datetime.datetime.utcnow()
                remaining_time = session["end_time"] - current_time
                if remaining_time.total_seconds() <= 0:
                    break

                participant_count = len(session["participants"])

                new_name = f"Sesh-{session['id']} | Ends in {remaining_time.seconds // 60}m | {participant_count} participants"
                await voice_channel.edit(name=new_name)
                
                # Check if all users have left the voice channel
                if len(voice_channel.members) == 0:
                    await voice_channel.delete()
                    return
                
                await asyncio.sleep(60)  # Update every minute

            # Delete the voice channel when the session ends
            await voice_channel.delete()

        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        async def ask_question(ctx, question, options):
            embed = discord.Embed(
                title="Sesh Setup",
                description=question,
                color=discord.Color.blue()
            )
            message = await ctx.send(embed=embed)
            for emoji in options:
                await message.add_reaction(emoji)

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in options

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                return str(reaction.emoji)
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond. Please try starting the session again.")
                return None

        duration = await ask_question(ctx, "Enter duration (15, 30, 45, 60)", ["1️⃣", "2️⃣", "3️⃣", "4️⃣"])
        if not duration:
            return
        duration = {"1️⃣": 15, "2️⃣": 30, "3️⃣": 45, "4️⃣": 60}[duration]

        session_time = datetime.datetime.utcnow()
        session_end_time = session_time + datetime.timedelta(minutes=duration)

        session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # Generate a unique 4-character session ID
        session = {
            "id": session_id,
            "time": session_time.isoformat(),
            "end_time": session_end_time.isoformat(),
            "creator": ctx.author.id,
            "participants": [{"id": ctx.author.id}]
        }

        async with self.config.guild(ctx.guild).sessions() as sessions:
            sessions.append(session)

        embed = discord.Embed(
            title="It's sesh time!",
            description=f"A new smoking session has started and will last for {duration} minutes.\n\n**Session ID:** {session_id}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Started by {ctx.author.display_name}")

        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            invite = await voice_channel.create_invite(max_age=duration * 60)
            embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)
        else:
            # Create a new voice channel named after the session ID
            voice_channel = await ctx.guild.create_voice_channel(name=f"Sesh-{session_id}", category=voice_channel_category)
            # Store the voice channel ID in the session data
            session["voice_channel_id"] = voice_channel.id
            invite = await voice_channel.create_invite(max_age=duration * 60)
            embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)

        if mention_role:
            await announcement_channel.send(f"{mention_role.mention}", embed=embed)
        else:
            await announcement_channel.send(embed=embed)

        self.bot.loop.create_task(update_channel_status(voice_channel, session))

    @commands.guild_only()
    @sesh.command()
    async def join(self, ctx):
        """Join the currently active smoking session."""
        async with self.config.guild(ctx.guild).sessions() as sessions:
            current_time = datetime.datetime.utcnow()
            for session in sessions:
                session_time = datetime.datetime.fromisoformat(session["time"])
                session_end_time = datetime.datetime.fromisoformat(session["end_time"])
                if session_time <= current_time < session_end_time:
                    if not any(p["id"] == ctx.author.id for p in session["participants"]):
                        session["participants"].append({
                            "id": ctx.author.id
                        })
                        await ctx.send(f"You have joined the smoking session at {session_time.strftime('%H:%M')}.")
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
                        session_time = datetime.datetime.fromisoformat(session["time"])
                        session["participants"].remove(participant)
                        await ctx.send(f"You have left the smoking session at {session_time.strftime('%H:%M')}.")
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
            participant_details = ", ".join([f"{self.bot.get_user(p['id']).name}" for p in session["participants"] if self.bot.get_user(p['id'])])
            session_time = datetime.datetime.fromisoformat(session["time"])
            embed.add_field(
                name=f"Session ID: {session['id']}",
                value=f"Time: {session_time.strftime('%H:%M')}\nCreator: {creator.name if creator else 'Unknown'}\nParticipants: {participant_details}",
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
                    if 'voice_channel_id' in session:
                        voice_channel = ctx.guild.get_channel(session['voice_channel_id'])
                        if voice_channel:
                            await voice_channel.delete()
                    sessions.remove(session)
                    await ctx.send(f"Smoking session with ID {session_id} has been cancelled.")
                    return
            await ctx.send("No session found with that ID or you are not the creator of the session.")

    @commands.guild_only()
    @sesh.command()
    async def end(self, ctx, session_id: str):
        """Manually end a smoking session.
        
        Provide the session ID to end the session.
        """
        async with self.config.guild(ctx.guild).sessions() as sessions:
            for session in sessions:
                if session["id"] == session_id:
                    if 'voice_channel_id' in session:
                        voice_channel = ctx.guild.get_channel(session['voice_channel_id'])
                        if voice_channel:
                            await voice_channel.delete()
                    sessions.remove(session)
                    await ctx.send(f"Smoking session with ID {session_id} has been manually ended.")
                    return
            await ctx.send("No session found with that ID.")

async def setup(bot):
    await bot.add_cog(Sesh(bot))
