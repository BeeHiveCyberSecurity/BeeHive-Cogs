import discord #type: ignore
from redbot.core import commands, Config #type: ignore
from redbot.core.bot import Red #type: ignore
from typing import List

class Meetings(commands.Cog):
    """Manage and schedule meetings."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "meetings": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    async def meeting(self, ctx: commands.Context):
        """Group command for managing meetings."""
        pass

    @meeting.command()
    async def create(self, ctx: commands.Context, name: str, description: str, time: str):
        """Create a new meeting."""
        guild = ctx.guild
        async with self.config.guild(guild).meetings() as meetings:
            if name in meetings:
                await ctx.send(f"A meeting with the name '{name}' already exists.")
                return
            meetings[name] = {
                "description": description,
                "time": time,
                "attendees": []
            }
        await ctx.send(f"Meeting '{name}' created successfully.")

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
            embed.add_field(name=name, value=f"Description: {details['description']}\nTime: {details['time']}\nAttendees: {len(details['attendees'])}", inline=False)
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
        embed.add_field(name="Time", value=details["time"], inline=False)
        embed.add_field(name="Attendees", value=attendee_names or "None", inline=False)
        await ctx.send(embed=embed)
