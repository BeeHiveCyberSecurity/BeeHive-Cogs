import discord #type: ignore
import asyncio
from redbot.core import commands, Config #type: ignore
from redbot.core.bot import Red #type: ignore
from typing import List
from datetime import datetime, timedelta
import pytz

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
            await ctx.send("You need to set your timezone before creating a meeting. Use the `!meeting settimezone <timezone>` command.")
            return

        await ctx.send("Let's start the meeting setup process. What will be the name of the meeting?")
        try:
            name_msg = await self.bot.wait_for('message', check=check, timeout=60)
            name = name_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Meeting setup cancelled.")
            return

        async with self.config.guild(ctx.guild).meetings() as meetings:
            if name in meetings:
                await ctx.send(f"A meeting with the name '{name}' already exists.")
                return

        await ctx.send("Please provide a description for the meeting.")
        try:
            description_msg = await self.bot.wait_for('message', check=check, timeout=60)
            description = description_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Meeting setup cancelled.")
            return

        await ctx.send(f"Please provide the time for the meeting (e.g., '2023-10-01 15:00' in your timezone: {user_timezone}).")
        try:
            time_msg = await self.bot.wait_for('message', check=check, timeout=60)
            time = time_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Meeting setup cancelled.")
            return

        await ctx.send("Please mention the users you want to invite to the meeting.")
        try:
            invite_msg = await self.bot.wait_for('message', check=check, timeout=60)
            users = invite_msg.mentions
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Meeting setup cancelled.")
            return

        async with self.config.guild(ctx.guild).meetings() as meetings:
            meetings[name] = {
                "description": description,
                "time": time,
                "attendees": [user.id for user in users],
                "creator_timezone": user_timezone
            }

        await ctx.send(f"Meeting '{name}' created successfully with {len(users)} attendees.")

    @meeting.command()
    async def invite(self, ctx: commands.Context, name: str, users: commands.Greedy[discord.Member]):
        """Invite users to a meeting."""
        guild = ctx.guild
        async with self.config.guild(guild).meetings() as meetings:
            if name not in meetings:
                await ctx.send(f"No meeting found with the name '{name}'.")
                return
            for user in users:
                if user.id not in meetings[name]["attendees"]:
                    meetings[name]["attendees"].append(user.id)
            await ctx.send(f"Users invited to the meeting '{name}'.")

    @meeting.command()
    async def list(self, ctx: commands.Context):
        """List all meetings."""
        guild = ctx.guild
        meetings = await self.config.guild(guild).meetings()
        if not meetings:
            await ctx.send("No meetings scheduled.")
            return
        embed = discord.Embed(title="Scheduled Meetings", color=discord.Color.blue())
        for name, details in meetings.items():
            embed.add_field(name=name, value=f"Description: {details['description']}\nTime: {details['time']} {details['creator_timezone']}\nAttendees: {len(details['attendees'])}", inline=False)
        await ctx.send(embed=embed)

    @meeting.command()
    async def details(self, ctx: commands.Context, name: str):
        """Get details of a specific meeting."""
        guild = ctx.guild
        meetings = await self.config.guild(guild).meetings()
        if name not in meetings:
            await ctx.send(f"No meeting found with the name '{name}'.")
            return
        details = meetings[name]
        attendees = [guild.get_member(user_id) for user_id in details["attendees"]]
        attendee_names = ", ".join([user.display_name for user in attendees if user])
        embed = discord.Embed(title=f"Meeting: {name}", color=discord.Color.green())
        embed.add_field(name="Description", value=details["description"], inline=False)
        embed.add_field(name="Time", value=f"{details['time']} {details['creator_timezone']}", inline=False)
        embed.add_field(name="Attendees", value=attendee_names or "None", inline=False)
        await ctx.send(embed=embed)


    @meeting.command()
    async def myschedule(self, ctx: commands.Context):
        """Check your upcoming meetings."""
        user_id = ctx.author.id
        guild = ctx.guild
        meetings = await self.config.guild(guild).meetings()
        user_meetings = [name for name, details in meetings.items() if user_id in details["attendees"]]
        if not user_meetings:
            await ctx.send("You have no upcoming meetings.")
            return
        embed = discord.Embed(title="Your Upcoming Meetings", color=discord.Color.purple())
        for name in user_meetings:
            details = meetings[name]
            embed.add_field(name=name, value=f"Description: {details['description']}\nTime: {details['time']} {details['creator_timezone']}", inline=False)
        await ctx.send(embed=embed)

    async def send_meeting_alert(self, meeting_name: str, guild: discord.Guild):
        """Send meeting alert to all attendees considering their timezones."""
        meetings = await self.config.guild(guild).meetings()
        if meeting_name not in meetings:
            return
        meeting = meetings[meeting_name]
        meeting_time_creator_tz = datetime.strptime(meeting["time"], "%Y-%m-%d %H:%M")
        creator_timezone = pytz.timezone(meeting["creator_timezone"])
        meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
        for user_id in meeting["attendees"]:
            user = guild.get_member(user_id)
            if user:
                user_timezone = await self.config.member(user).timezone()
                user_time = meeting_time_utc.astimezone(pytz.timezone(user_timezone))
                await user.send(f"Reminder: The meeting '{meeting_name}' is scheduled for {user_time.strftime('%Y-%m-%d %H:%M %Z')} in your timezone.")

    async def check_meetings(self):
        """Check for upcoming meetings and send alerts."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                meetings = await self.config.guild(guild).meetings()
                for name, details in meetings.items():
                    creator_timezone = pytz.timezone(details["creator_timezone"])
                    meeting_time_creator_tz = datetime.strptime(details["time"], "%Y-%m-%d %H:%M")
                    meeting_time_utc = creator_timezone.localize(meeting_time_creator_tz).astimezone(pytz.utc)
                    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                    if now_utc + timedelta(minutes=10) >= meeting_time_utc > now_utc:
                        await self.send_meeting_alert(name, guild)
            await asyncio.sleep(60)  # Check every minute

    @meeting.command()
    async def timezones(self, ctx: commands.Context):
        """List all timezones and their current times."""
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        embed = discord.Embed(title="Available Timezones", color=discord.Color.orange())
        for timezone in pytz.all_timezones:
            local_time = now_utc.astimezone(pytz.timezone(timezone))
            embed.add_field(name=timezone, value=local_time.strftime('%Y-%m-%d %H:%M %Z'), inline=False)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.group()
    async def meetingset(self, ctx: commands.Context):
        """Group command for managing meetings."""

    @meetingset.command()
    async def settimezone(self, ctx: commands.Context, timezone: str):
        """Set your timezone."""
        if timezone not in pytz.all_timezones:
            await ctx.send("Invalid timezone. Please provide a valid timezone from the IANA timezone database.")
            return
        await self.config.member(ctx.author).timezone.set(timezone)
        await ctx.send(f"Your timezone has been set to {timezone}.")

