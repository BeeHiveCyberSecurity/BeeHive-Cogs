import discord #type: ignore
import asyncio
from redbot.core import commands, Config #type: ignore
from redbot.core.bot import Red #type: ignore
from typing import List
from datetime import datetime, timedelta
import pytz #type: ignore
import random
import string

class Meetings(commands.Cog):
    """Manage and schedule meetings."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "meetings": {}
        }
        default_member = {
            "timezone": "UTC"
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)
        self.bot.loop.create_task(self.check_meetings())

    def generate_meeting_id(self):
        """Generate a random 4 character meeting ID."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    @commands.guild_only()
    @commands.group()
    async def meeting(self, ctx: commands.Context):
        """Group command for managing meetings."""
        pass

    @meeting.command()
    async def create(self, ctx: commands.Context):
        """Start the setup process to create a new meeting."""
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        user_timezone = await self.config.member(ctx.author).timezone()
        if user_timezone == "UTC":
            embed = discord.Embed(
                title="No user timezone",
                description="You need to set your timezone before creating a meeting. Use the `!meetingset timezone` command.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        await ctx.send("Let's start the meeting setup process. What will be the name of the meeting?")
        try:
            name_msg = await self.bot.wait_for('message', check=check, timeout=60)
            name = name_msg.content
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="You took too long to respond. Meeting setup cancelled.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        async with self.config.guild(ctx.guild).meetings() as meetings:
            if any(meeting["name"] == name for meeting in meetings.values()):
                embed = discord.Embed(
                    title="Meeting name already taken",
                    description=f"A meeting with the name '{name}' already exists.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

        await ctx.send("Please provide a description for the meeting.")
        try:
            description_msg = await self.bot.wait_for('message', check=check, timeout=60)
            description = description_msg.content
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="You took too long to respond. Meeting setup cancelled.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        now = datetime.now(pytz.timezone(user_timezone))
        today = now.strftime("%B %d, %Y")
        tomorrow = (now + timedelta(days=1)).strftime("%B %d, %Y")
        embed = discord.Embed(
            title="Meeting Time",
            description=f"Please provide the date and time for the meeting (e.g., 'October 1, 2023 at 3:00 PM' in your timezone: {user_timezone}).\nFor reference, today is {today} and tomorrow is {tomorrow}.",
            color=0x2bbd8e
        )
        await ctx.send(embed=embed)
        try:
            time_msg = await self.bot.wait_for('message', check=check, timeout=60)
            time = time_msg.content
            # Validate time format
            try:
                meeting_time = datetime.strptime(time, "%B %d, %Y at %I:%M %p")
                meeting_time = pytz.timezone(user_timezone).localize(meeting_time)
            except ValueError:
                embed = discord.Embed(
                    title="Invalid time format",
                    description="Invalid time format. Please use 'Month Day, Year at HH:MM AM/PM'.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="You took too long to respond. Meeting setup cancelled.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        await ctx.send("How long will the meeting last? Please provide the duration in minutes.")
        try:
            duration_msg = await self.bot.wait_for('message', check=check, timeout=60)
            duration = int(duration_msg.content)
            if duration <= 0:
                raise ValueError("Duration must be a positive integer.")
        except (asyncio.TimeoutError, ValueError):
            embed = discord.Embed(
                title="Invalid duration",
                description="Invalid duration. Please provide a positive integer for the duration in minutes.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        await ctx.send("Please mention the users you want to invite to the meeting.")
        try:
            invite_msg = await self.bot.wait_for('message', check=check, timeout=60)
            users = invite_msg.mentions
            if not users:
                embed = discord.Embed(
                    title="No attendees added",
                    description="You can't have a meeting all by yourself, silly...",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="You took too long to respond. Meeting setup cancelled.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        # Add the command author to the list of attendees
        users.append(ctx.author)

        meeting_id = self.generate_meeting_id()
        async with self.config.guild(ctx.guild).meetings() as meetings:
            meetings[meeting_id] = {
                "name": name,
                "description": description,
                "time": meeting_time.strftime("%Y-%m-%d %H:%M"),
                "duration": duration,
                "attendees": [user.id for user in users],
                "creator_timezone": user_timezone
            }

        timestamp = int(meeting_time.timestamp())
        end_time = meeting_time + timedelta(minutes=duration)
        end_timestamp = int(end_time.timestamp())
        embed = discord.Embed(
            title="Meeting created",
            description=f"Your meeting is successfully setup! Here's the summary...",
            color=0x2bbd8e
        )
        embed.add_field(name="Meeting ID", value=f"Your meeting ID is `{meeting_id}`\nSave this for your records, you'll need it to fetch information about this meeting's details, or to cancel this meeting.", inline=False)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Description", value=description, inline=True)
        embed.add_field(name="Time", value=f"<t:{timestamp}:F> to <t:{end_timestamp}:F> (<t:{timestamp}:R>) {user_timezone}", inline=True)
        embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
        embed.add_field(name="Attendees", value=", ".join([user.mention for user in users]), inline=False)
        await ctx.send(embed=embed)

    @meeting.command()
    async def invite(self, ctx: commands.Context, meeting_id: str, users: commands.Greedy[discord.Member]):
        """Invite users to a meeting."""
        guild = ctx.guild
        async with self.config.guild(guild).meetings() as meetings:
            if meeting_id not in meetings:
                embed = discord.Embed(
                    title="Meeting Not Found",
                    description=f"No meeting found with the ID '{meeting_id}'.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
            for user in users:
                if user.id not in meetings[meeting_id]["attendees"]:
                    meetings[meeting_id]["attendees"].append(user.id)
            embed = discord.Embed(
                title="Users Invited",
                description=f"Users invited to the meeting '{meetings[meeting_id]['name']}'.",
                color=0x2bbd8e
            )
            await ctx.send(embed=embed)

    @meeting.command()
    async def delete(self, ctx: commands.Context, meeting_id: str):
        """Delete a meeting by its ID."""
        guild = ctx.guild
        async with self.config.guild(guild).meetings() as meetings:
            if meeting_id not in meetings:
                embed = discord.Embed(
                    title="Meeting Not Found",
                    description=f"No meeting found with the ID '{meeting_id}'.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
            
            meeting = meetings[meeting_id]
            if ctx.author.id not in meeting["attendees"]:
                embed = discord.Embed(
                    title="Permission denied",
                    description="Only an invited attendee can delete this meeting.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

            del meetings[meeting_id]
            embed = discord.Embed(
                title="Meeting Deleted",
                description=f"Meeting with ID '{meeting_id}' has been deleted.",
                color=0x2bbd8e
            )
            await ctx.send(embed=embed)

    @meeting.command()
    async def list(self, ctx: commands.Context):
        """List all meetings."""
        guild = ctx.guild
        meetings = await self.config.guild(guild).meetings()
        if not meetings:
            embed = discord.Embed(
                title="No Meetings",
                description="No meetings scheduled.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title="Scheduled meetings", color=0xfffffe)
        for meeting_id, details in meetings.items():
            meeting_time_creator_tz = datetime.strptime(details["time"], "%Y-%m-%d %H:%M")
            creator_timezone = pytz.timezone(details["creator_timezone"])
            meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
            timestamp = int(meeting_time_utc.timestamp())
            end_time_utc = meeting_time_utc + timedelta(minutes=details["duration"])
            end_timestamp = int(end_time_utc.timestamp())
            embed.add_field(
                name=f"{details['name']} ({meeting_id})",
                value=f"> {details['description']}\n- **<t:{timestamp}:F> to <t:{end_timestamp}:F>**, **<t:{timestamp}:R>**\n- **{len(details['attendees'])}** attendees",
                inline=False
            )
        await ctx.send(embed=embed)

    @meeting.command()
    async def details(self, ctx: commands.Context, meeting_id: str):
        """Get details of a specific meeting."""
        guild = ctx.guild
        meetings = await self.config.guild(guild).meetings()
        if meeting_id not in meetings:
            embed = discord.Embed(
                title="Meeting Not Found",
                description=f"No meeting found with the ID '{meeting_id}'.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        details = meetings[meeting_id]
        attendees = [guild.get_member(user_id) for user_id in details["attendees"]]
        attendee_names = ", ".join([user.display_name for user in attendees if user])
        
        meeting_time_creator_tz = datetime.strptime(details["time"], "%Y-%m-%d %H:%M")
        creator_timezone = pytz.timezone(details["creator_timezone"])
        meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
        timestamp = int(meeting_time_utc.timestamp())
        end_time_utc = meeting_time_utc + timedelta(minutes=details["duration"])
        end_timestamp = int(end_time_utc.timestamp())
        
        embed = discord.Embed(title=f"Meeting: {details['name']} (ID: {meeting_id})", color=0x2bbd8e)
        embed.add_field(name="Description", value=details["description"], inline=False)
        embed.add_field(name="Time", value=f"<t:{timestamp}:F> to <t:{end_timestamp}:F> (<t:{timestamp}:R>)", inline=False)
        embed.add_field(name="Duration", value=f"{details['duration']} minutes", inline=False)
        embed.add_field(name="Attendees", value=attendee_names or "None", inline=False)
        await ctx.send(embed=embed)


    @meeting.command()
    async def myschedule(self, ctx: commands.Context):
        """Check your upcoming and active meetings."""
        user_id = ctx.author.id
        guild = ctx.guild
        meetings = await self.config.guild(guild).meetings()
        user_meetings = [(meeting_id, details) for meeting_id, details in meetings.items() if user_id in details["attendees"]]
        if not user_meetings:
            embed = discord.Embed(
                title="Here's your schedule",
                description="You have no upcoming or active meetings. Book a new meeting with another user using `meeting create`.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title="Your Upcoming and Active Meetings", color=0xfffffe)
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        for meeting_id, details in user_meetings:
            meeting_time_creator_tz = datetime.strptime(details["time"], "%Y-%m-%d %H:%M")
            creator_timezone = pytz.timezone(details["creator_timezone"])
            meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
            timestamp = int(meeting_time_utc.timestamp())
            end_time_utc = meeting_time_utc + timedelta(minutes=details["duration"])
            end_timestamp = int(end_time_utc.timestamp())
            status = "Active" if now_utc >= meeting_time_utc else "Upcoming"
            embed.add_field(
                name=f"{details['name']} (ID: {meeting_id})",
                value=f"Description: {details['description']}\nTime: <t:{timestamp}:F> to <t:{end_timestamp}:F> (<t:{timestamp}:R>)\nDuration: {details['duration']} minutes\nStatus: {status}",
                inline=False
            )
        await ctx.send(embed=embed)

    async def send_meeting_alert(self, meeting_id: str, guild: discord.Guild):
        """Send meeting alert to all attendees considering their timezones."""
        meetings = await self.config.guild(guild).meetings()
        if meeting_id not in meetings:
            return
        meeting = meetings[meeting_id]
        meeting_time_creator_tz = datetime.strptime(meeting["time"], "%Y-%m-%d %H:%M")
        creator_timezone = pytz.timezone(meeting["creator_timezone"])
        meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
        for user_id in meeting["attendees"]:
            user = guild.get_member(user_id)
            if user:
                user_timezone = await self.config.member(user).timezone()
                user_time = meeting_time_utc.astimezone(pytz.timezone(user_timezone))
                await user.send(f"Reminder: The meeting '{meeting['name']}' (ID: {meeting_id}) is scheduled for {user_time.strftime('%Y-%m-%d %H:%M %Z')} in your timezone.")

    async def check_meetings(self):
        """Check for upcoming meetings and send alerts."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                meetings = await self.config.guild(guild).meetings()
                for meeting_id, details in meetings.items():
                    creator_timezone = pytz.timezone(details["creator_timezone"])
                    meeting_time_creator_tz = datetime.strptime(details["time"], "%Y-%m-%d %H:%M")
                    meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
                    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                    if now_utc + timedelta(minutes=10) >= meeting_time_utc > now_utc:
                        await self.send_meeting_alert(meeting_id, guild)
            await asyncio.sleep(60)  # Check every minute

    @meeting.command()
    async def timezones(self, ctx: commands.Context):
        """List all timezones and their current times."""
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        timezones = pytz.all_timezones
        pages = [timezones[i:i + 25] for i in range(0, len(timezones), 25)]
        current_page = 0

        def generate_embed(page):
            embed = discord.Embed(title="Current times in various timezones", color=0xfffffe)
            for timezone in pages[page]:
                local_time = now_utc.astimezone(pytz.timezone(timezone))
                timestamp = int(local_time.timestamp())
                embed.add_field(name=timezone, value=f"<t:{timestamp}:F>", inline=True)
            embed.set_footer(text=f"Page {page + 1} of {len(pages)}")
            return embed

        message = await ctx.send(embed=generate_embed(current_page))

        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        await message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=120)
                if str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                    current_page += 1
                elif str(reaction.emoji) == "❌":
                    await message.delete()
                    break
                await message.edit(embed=generate_embed(current_page))
                await message.remove_reaction(reaction.emoji, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    @commands.guild_only()
    @commands.group()
    async def meetingset(self, ctx: commands.Context):
        """Group command for managing meetings."""
        pass

    @meetingset.command()
    async def timezone(self, ctx: commands.Context, timezone: str):
        """Set your timezone."""
        if timezone not in pytz.all_timezones:
            embed = discord.Embed(
                title="Invalid timezone",
                description="Invalid timezone. Please provide a valid timezone from the IANA timezone database.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        await self.config.member(ctx.author).timezone.set(timezone)
        embed = discord.Embed(
            title="Timezone set",
            description=f"Your timezone has been set to **{timezone}**.",
            color=0x2bbd8e
        )
        await ctx.send(embed=embed)

