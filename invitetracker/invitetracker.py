import discord
from redbot.core import commands, Config, checks

class InviteTracker(commands.Cog):
    """Tracks user invites with customizable announcements, rewards, and perks."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "invites": {},
            "rewards": {},
            "announcement_channel": None,
        }
        self.config.register_guild(**default_guild)
        self.invites = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.invites[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        invites_before = self.invites[guild.id]
        invites_after = await guild.invites()
        self.invites[guild.id] = invites_after

        for invite in invites_before:
            if invite.uses < self.get_invite_uses(invites_after, invite.code):
                inviter = invite.inviter
                await self.update_invites(guild, inviter)
                await self.announce_invite(guild, member, inviter)
                await self.check_rewards(guild, inviter)
                break

    def get_invite_uses(self, invites, code):
        for invite in invites:
            if invite.code == code:
                return invite.uses
        return 0

    async def update_invites(self, guild, inviter):
        async with self.config.guild(guild).invites() as invites:
            if str(inviter.id) not in invites:
                invites[str(inviter.id)] = 0
            invites[str(inviter.id)] += 1

    async def announce_invite(self, guild, member, inviter):
        channel_id = await self.config.guild(guild).announcement_channel()
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(f"{member.mention} joined using {inviter.mention}'s invite!")

    async def check_rewards(self, guild, inviter):
        invites = await self.config.guild(guild).invites()
        rewards = await self.config.guild(guild).rewards()
        invite_count = invites.get(str(inviter.id), 0)

        for count, reward in rewards.items():
            if invite_count == int(count):
                role = guild.get_role(reward)
                if role:
                    await inviter.add_roles(role)
                    await inviter.send(f"Congratulations! You've been awarded the {role.name} role for inviting {count} members!")

    @commands.guild_only()
    @commands.admin()
    @commands.group()
    async def invitetracker(self, ctx):
        """Settings for the invite tracker."""
        pass

    @invitetracker.command()
    async def announcechannel(self, ctx, channel: discord.TextChannel):
        """Set the announcement channel for invites."""
        await self.config.guild(ctx.guild).announcement_channel.set(channel.id)
        await ctx.send(f"Announcement channel set to {channel.mention}")

    @invitetracker.command()
    async def addreward(self, ctx, invite_count: int, role: discord.Role):
        """Add a reward for a specific number of invites."""
        async with self.config.guild(ctx.guild).rewards() as rewards:
            rewards[str(invite_count)] = role.id
        await ctx.send(f"Reward set: {role.name} for {invite_count} invites")

    @invitetracker.command()
    async def removereward(self, ctx, invite_count: int):
        """Remove a reward for a specific number of invites."""
        async with self.config.guild(ctx.guild).rewards() as rewards:
            if str(invite_count) in rewards:
                del rewards[str(invite_count)]
                await ctx.send(f"Reward for {invite_count} invites removed")
            else:
                await ctx.send(f"No reward found for {invite_count} invites")

def setup(bot):
    bot.add_cog(InviteTracker(bot))
