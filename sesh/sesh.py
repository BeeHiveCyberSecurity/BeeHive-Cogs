from redbot.core import commands, Config #type: ignore
import discord #type: ignore
import datetime
import asyncio
import uuid

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

                participant_types = [p["type"] for p in session["participants"]]
                most_popular_type = max(set(participant_types), key=participant_types.count)
                participant_count = len(session["participants"])

                new_name = f"Sesh-{session['id']} | Ends in {remaining_time.seconds // 60}m | {most_popular_type} | {participant_count} participants"
                await voice_channel.edit(name=new_name)
                await asyncio.sleep(60)  # Update every minute

            # Delete the voice channel when the session ends
            await voice_channel.delete()

        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        # Step 1: Ask for session description
        await ctx.send("Please provide a description for the session:")

        def check_message(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            description_msg = await self.bot.wait_for('message', check=check_message, timeout=60.0)
            description = description_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please try starting the session again.")
            return

        # Step 2: Ask for session duration
        options = [
            discord.SelectOption(label="15 minutes", value="15"),
            discord.SelectOption(label="30 minutes", value="30"),
            discord.SelectOption(label="45 minutes", value="45"),
            discord.SelectOption(label="1 hour", value="60")
        ]

        select = discord.ui.Select(placeholder="Select session duration", options=options)

        async def select_callback(interaction):
            session_duration = int(interaction.data['values'][0])
            session_time = datetime.datetime.utcnow()
            session_end_time = session_time + datetime.timedelta(minutes=session_duration)

            # Step 3: Ask for marijuana type
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
                await ctx.send("You took too long to respond. Please try starting the session again.")
                return

            try:
                strain_interaction = await self.bot.wait_for('interaction', check=check_type, timeout=60.0)
                strain_type = strain_interaction.data['custom_id']
                await strain_interaction.response.send_message(f"You selected {strain_type}. The session is now starting.")
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond. Please try starting the session again.")
                return

            session_id = str(uuid.uuid4())  # Generate a unique session ID
            session = {
                "id": session_id,
                "time": session_time.isoformat(),
                "end_time": session_end_time.isoformat(),
                "description": description,
                "creator": ctx.author.id,
                "participants": [{"id": ctx.author.id, "type": marijuana_type, "strain": strain_type}]
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
                voice_channel = await ctx.guild.create_voice_channel(name=f"Sesh-{session_id}", category=voice_channel_category)
                # Store the voice channel ID in the session data
                session["voice_channel_id"] = voice_channel.id
                invite = await voice_channel.create_invite(max_age=session_duration * 60)
                embed.add_field(name="Voice Channel", value=f"[Join Voice Channel]({invite.url})", inline=False)

            if mention_role:
                await announcement_channel.send(f"{mention_role.mention}", embed=embed)
            else:
                await announcement_channel.send(embed=embed)

            self.bot.loop.create_task(update_channel_status(voice_channel, session))

            # Disable the select menu to prevent further interaction
            for item in view.children:
                item.disabled = True
            await interaction.message.edit(view=view)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await ctx.send("Select the session duration:", view=view)

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
                        await ctx.send(f"You have joined the smoking session at {session_time.strftime('%H:%M')} with {marijuana_type} ({strain_type}).")
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
            participant_details = ", ".join([f"{self.bot.get_user(p['id']).name} ({p['type']}, {p['strain']})" for p in session["participants"] if self.bot.get_user(p['id'])])
            session_time = datetime.datetime.fromisoformat(session["time"])
            embed.add_field(
                name=f"Session ID: {session['id']}",
                value=f"Time: {session_time.strftime('%H:%M')}\nDescription: {session['description']}\nCreator: {creator.name if creator else 'Unknown'}\nParticipants: {participant_details}",
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
