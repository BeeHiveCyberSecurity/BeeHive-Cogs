import discord
from redbot.core import commands, Config
from datetime import datetime, timedelta

class StaffManager(commands.Cog):
    """Manage and track staff activities"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_member = {
            "is_staff": False,
            "staff_since": None,
            "punishments_issued": 0,
            "suspended": False,
            "suspension_reason": None,
            "suspension_end": None,
            "original_roles": [],
        }
        default_guild = {
            "staff_roles": {}
        }
        self.config.register_member(**default_member)
        self.config.register_guild(**default_guild)

    @commands.group()
    async def staffmanager(self, ctx):
        """Group for staff management commands"""
        pass

    @staffmanager.command()
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, role: discord.Role, role_type: str):
        """Add a role as a staff role with a specific type (e.g., mod, admin, helper)"""
        async with self.config.guild(ctx.guild).staff_roles() as staff_roles:
            staff_roles[role.id] = role_type
        await ctx.send(f"Role {role.name} has been added as a {role_type} staff role.")

    @staffmanager.command()
    async def info(self, ctx, member: discord.Member):
        """Get information about a staff member"""
        member_data = await self.config.member(member).all()
        if not member_data["is_staff"]:
            await ctx.send(f"{member.display_name} is not a staff member.")
            return

        staff_since = member_data["staff_since"]
        punishments_issued = member_data["punishments_issued"]
        suspended = member_data["suspended"]
        suspension_reason = member_data["suspension_reason"] or "N/A"
        suspension_end = member_data["suspension_end"]

        embed = discord.Embed(title=f"Staff Info: {member.display_name}", color=discord.Color.blue())
        embed.add_field(name="Staff Since", value=staff_since or "N/A", inline=False)
        embed.add_field(name="Punishments Issued", value=punishments_issued, inline=False)
        embed.add_field(name="Suspended", value="Yes" if suspended else "No", inline=False)
        if suspended:
            embed.add_field(name="Suspension Reason", value=suspension_reason, inline=False)
            embed.add_field(name="Suspension Ends", value=suspension_end or "N/A", inline=False)

        await ctx.send(embed=embed)

    @staffmanager.command()
    async def list(self, ctx):
        """List all staff members and their tenure"""
        guild = ctx.guild
        members = guild.members
        staff_list = []

        for member in members:
            member_data = await self.config.member(member).all()
            if member_data["is_staff"]:
                staff_since = member_data["staff_since"]
                tenure = "N/A"
                if staff_since:
                    staff_since_date = datetime.fromisoformat(staff_since)
                    tenure = (datetime.utcnow() - staff_since_date).days
                staff_list.append((member.display_name, tenure))

        if not staff_list:
            await ctx.send("There are no staff members currently.")
            return

        embed = discord.Embed(title="Staff Members List", color=discord.Color.green())
        for name, tenure in staff_list:
            embed.add_field(name=name, value=f"Tenure: {tenure} days", inline=False)

        await ctx.send(embed=embed)

    @staffmanager.command()
    @commands.is_owner()
    async def suspend(self, ctx, member: discord.Member, days: int, *, reason: str):
        """Temporarily suspend a staff member's role for a specified reason"""
        member_data = await self.config.member(member).all()
        if not member_data["is_staff"]:
            await ctx.send(f"{member.display_name} is not a staff member.")
            return

        if member_data["suspended"]:
            await ctx.send(f"{member.display_name} is already suspended.")
            return

        guild = ctx.guild
        staff_roles = [role for role in member.roles if role.id in (await self.config.guild(guild).staff_roles()).keys()]

        await self.config.member(member).suspended.set(True)
        await self.config.member(member).suspension_reason.set(reason)
        await self.config.member(member).suspension_end.set((datetime.utcnow() + timedelta(days=days)).isoformat())
        await self.config.member(member).original_roles.set([role.id for role in staff_roles])

        await member.remove_roles(*staff_roles, reason="Suspended by command")
        await ctx.send(f"{member.display_name} has been suspended for: {reason}")

        suspension_embed = discord.Embed(
            title="Suspension Notice",
            description=f"You have been suspended from staff roles.",
            color=discord.Color.red()
        )
        suspension_embed.add_field(name="Reason", value=reason, inline=False)
        suspension_embed.add_field(name="Duration", value=f"{days} days", inline=False)

        try:
            await member.send(embed=suspension_embed)
        except discord.Forbidden:
            await ctx.send(f"Could not send a DM to {member.display_name}. They might have DMs disabled.")

        await self.bot.loop.create_task(self.restore_roles_after_suspension(member, days))

    async def restore_roles_after_suspension(self, member, days):
        await asyncio.sleep(days * 86400)  # Convert days to seconds
        member_data = await self.config.member(member).all()
        if member_data["suspended"]:
            guild = member.guild
            original_roles_ids = member_data["original_roles"]
            original_roles = [guild.get_role(role_id) for role_id in original_roles_ids if guild.get_role(role_id)]

            await member.add_roles(*original_roles, reason="Suspension expired")
            await self.config.member(member).suspended.set(False)
            await self.config.member(member).suspension_reason.set(None)
            await self.config.member(member).suspension_end.set(None)
            await self.config.member(member).original_roles.set([])

            restoration_embed = discord.Embed(
                title="Suspension Ended",
                description="Your suspension has ended, and your roles have been restored.",
                color=discord.Color.green()
            )

            try:
                await member.send(embed=restoration_embed)
            except discord.Forbidden:
                pass
