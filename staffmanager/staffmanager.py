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
        self.config.register_member(**default_member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Check for role changes to update staff status"""
        if before.roles == after.roles:
            return

        guild = after.guild
        mod_role = guild.get_role(guild.settings.mod_role)
        admin_role = guild.get_role(guild.settings.admin_role)

        is_staff = any(role in after.roles for role in [mod_role, admin_role])
        member_data = await self.config.member(after).all()

        if is_staff and not member_data["is_staff"]:
            await self.config.member(after).is_staff.set(True)
            await self.config.member(after).staff_since.set(datetime.utcnow().isoformat())
        elif not is_staff and member_data["is_staff"]:
            await self.config.member(after).is_staff.set(False)
            await self.config.member(after).staff_since.set(None)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Automatically count punishments when a member is banned"""
        member_data = await self.config.member(user).all()
        if member_data["is_staff"]:
            new_count = member_data["punishments_issued"] + 1
            await self.config.member(user).punishments_issued.set(new_count)

    @commands.command()
    async def staffinfo(self, ctx, member: discord.Member):
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

    @commands.command()
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
        mod_role = guild.get_role(guild.settings.mod_role)
        admin_role = guild.get_role(guild.settings.admin_role)
        staff_roles = [role for role in [mod_role, admin_role] if role in member.roles]

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
