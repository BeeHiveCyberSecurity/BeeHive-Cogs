import discord #type: ignore
from redbot.core import commands, Config, checks #type: ignore
import matplotlib.pyplot as plt #type: ignore
import io
import asyncio

class Invites(commands.Cog):
    """Tracks user invites with customizable announcements, rewards, and perks."""

    DISBOARD_BOT_ID = 302050872383242240

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "invites": {},
            "rewards": {},
            "announcement_channel": None,
            "member_growth": []
        }
        self.config.register_guild(**default_guild)
        self.invites = {}
        self.milestones = [1, 2, 3, 4, 5, 10, 15, 20]

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except Exception as e:
                print(f"Failed to fetch invites for guild {guild.id}: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        try:
            invites_before = self.invites.get(guild.id, [])
            invites_after = await guild.invites()
            self.invites[guild.id] = invites_after

            for invite in invites_before:
                if invite.uses < self.get_invite_uses(invites_after, invite.code):
                    inviter = invite.inviter
                    if inviter and inviter.id == self.DISBOARD_BOT_ID:
                        print(f"Invite by Disboard bot ignored for guild {guild.id}")
                        return
                    if inviter:
                        await self.update_invites(guild, inviter)
                        await self.announce_invite(guild, member, inviter)
                        await self.check_rewards(guild, inviter)
                    break

            # Update member growth
            async with self.config.guild(guild).member_growth() as growth:
                growth.append((member.joined_at.isoformat(), guild.member_count))

        except Exception as e:
            print(f"Error processing member join for guild {guild.id}: {e}")

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
        try:
            channel_id = await self.config.guild(guild).announcement_channel()
            announcement_channel = guild.get_channel(channel_id) if channel_id else None
            if announcement_channel:
                embed = discord.Embed(
                    title="New Member Joined",
                    description=f"{member.mention} joined using {inviter.mention}'s invite!",
                    color=discord.Color.from_str("#2bbd8e")
                )
                await announcement_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to announce invite in guild {guild.id}: {e}")

    async def check_rewards(self, guild, inviter):
        try:
            invites = await self.config.guild(guild).invites()
            rewards = await self.config.guild(guild).rewards()
            invite_count = invites.get(str(inviter.id), 0)

            for count, reward in rewards.items():
                if invite_count == int(count):
                    role = guild.get_role(reward)
                    if role:
                        await inviter.add_roles(role)
                        embed = discord.Embed(
                            title="Reward Earned",
                            description=f"Congratulations! You've been awarded the {role.name} role for inviting {count} members!",
                            color=discord.Color.from_str("#2bbd8e")
                        )
                        await self.announce_reward(guild, inviter, embed)
        except Exception as e:
            print(f"Failed to check rewards for inviter {inviter.id} in guild {guild.id}: {e}")

    async def announce_reward(self, guild, inviter, embed):
        try:
            channel_id = await self.config.guild(guild).announcement_channel()
            announcement_channel = guild.get_channel(channel_id) if channel_id else None
            if announcement_channel:
                await announcement_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to announce reward in guild {guild.id}: {e}")

    @commands.guild_only()
    @commands.admin()
    @commands.group()
    async def invites(self, ctx):
        """Settings for the invite tracker."""
        pass

    @invites.command()
    async def announcechannel(self, ctx, channel: str):
        """Set the announcement channel for invites. Use 'none' to clear the channel."""
        if channel.lower() == "none":
            await self.config.guild(ctx.guild).announcement_channel.clear()
            embed = discord.Embed(
                title="Announcement Channel Cleared",
                description="The announcement channel has been cleared.",
                color=discord.Color.from_str("#ff4545")
            )
        else:
            channel_obj = discord.utils.get(ctx.guild.text_channels, mention=channel) or discord.utils.get(ctx.guild.text_channels, name=channel)
            if channel_obj:
                await self.config.guild(ctx.guild).announcement_channel.set(channel_obj.id)
                embed = discord.Embed(
                    title="Announcement Channel Set",
                    description=f"Announcement channel set to {channel_obj.mention}",
                    color=discord.Color.from_str("#2bbd8e")
                )
            else:
                embed = discord.Embed(
                    title="Channel Not Found",
                    description="The specified channel could not be found.",
                    color=discord.Color.from_str("#ff4545")
                )
        await ctx.send(embed=embed)

    @invites.command()
    async def addreward(self, ctx, invite_count: int, role: discord.Role):
        """Add a reward for a specific number of invites."""
        async with self.config.guild(ctx.guild).rewards() as rewards:
            rewards[str(invite_count)] = role.id
        embed = discord.Embed(
            title="Reward Added",
            description=f"Reward set: {role.name} for {invite_count} invites",
            color=discord.Color.from_str("#2bbd8e")
        )
        await ctx.send(embed=embed)

    @invites.command()
    async def removereward(self, ctx, invite_count: int):
        """Remove a reward for a specific number of invites."""
        async with self.config.guild(ctx.guild).rewards() as rewards:
            if str(invite_count) in rewards:
                del rewards[str(invite_count)]
                embed = discord.Embed(
                    title="Reward Removed",
                    description=f"Reward for {invite_count} invites removed",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="No Reward Found",
                    description=f"No reward found for {invite_count} invites",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)

    @invites.command()
    async def leaderboard(self, ctx):
        """Show the leaderboard of top inviting users."""
        invites = await self.config.guild(ctx.guild).invites()
        sorted_invites = sorted(invites.items(), key=lambda item: item[1], reverse=True)
        leaderboard = []

        for inviter_id, count in sorted_invites[:10]:  # Top 10 inviters
            inviter = ctx.guild.get_member(int(inviter_id))
            if inviter:
                leaderboard.append(f"{inviter.mention}: {count} invites")

        if leaderboard:
            embed = discord.Embed(
                title="Top Inviters",
                description="\n".join(leaderboard),
                color=discord.Color.from_str("#2bbd8e")
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No invites recorded",
                description="No invites tracked yet. Invites can only be tracked from the point the module is loaded and the bot is present in the server, moving forward.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)

    @invites.command()
    async def chart(self, ctx):
        """graph the server's growth"""
        growth = await self.config.guild(ctx.guild).member_growth()
        if not growth:
            await ctx.send("No member growth data available.")
            return

        # Summarize the data by day
        summarized_growth = {}
        for entry in growth:
            date = entry[0].split("T")[0]  # Extract the date part only
            member_count = entry[1]
            if date not in summarized_growth:
                summarized_growth[date] = member_count

        dates = list(summarized_growth.keys())
        member_counts = list(summarized_growth.values())

        # Convert dates to "X days ago" or "X hours ago"
        from datetime import datetime, timedelta

        def format_date(date_str):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            now = datetime.now()
            delta = now - date_obj
            if delta.days > 0:
                return f"{delta.days} days ago"
            else:
                hours = delta.seconds // 3600
                return f"{hours} hours ago"

        formatted_dates = [format_date(date) for date in dates]

        plt.figure(figsize=(10, 5))
        plt.plot_date([datetime.strptime(date, "%Y-%m-%d") for date in dates], member_counts, marker='o', linestyle='-')
        plt.title('Server member growth')
        plt.xlabel('Date')
        plt.ylabel('Member count')
        
        # Display fewer date labels to reduce cramping
        max_labels = 10
        if len(dates) > max_labels:
            step = len(dates) // max_labels
            plt.xticks([datetime.strptime(date, "%Y-%m-%d") for date in dates[::step]], formatted_dates[::step], rotation=45, ha='right')
        else:
            plt.xticks([datetime.strptime(date, "%Y-%m-%d") for date in dates], formatted_dates, rotation=45, ha='right')
        
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        file = discord.File(buf, filename='member_growth.png')

        await ctx.send(file=file)

    @invites.command()
    async def stats(self, ctx):
        """Fetch and show invite stats for the server."""
        invites = await ctx.guild.invites()
        if not invites:
            await ctx.send("No invite stats available.")
            return

        pages = []
        for invite in invites:
            inviter = invite.inviter
            uses = invite.uses
            embed = discord.Embed(
                title="Invite stats",
                color=discord.Color.from_str("#2bbd8e")
            )
            embed.add_field(name="Invite code", value=f"**`{invite.code}`**", inline=True)
            embed.add_field(name="Inviter", value=f"{inviter.mention if inviter else 'Unknown'}", inline=True)
            embed.add_field(name="Uses", value=f"**`{uses}`**", inline=True)
            pages.append(embed)

        if not pages:
            await ctx.send("No invite stats available.")
            return

        message = await ctx.send(embed=pages[0])

        await message.add_reaction("⬅️")
        await message.add_reaction("❌")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"]

        i = 0
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "➡️":
                    i += 1
                elif str(reaction.emoji) == "⬅️":
                    i -= 1
                elif str(reaction.emoji) == "❌":
                    await message.delete()
                    # return instead of breaking so we don't try to clear reactions on a message that no longer exists
                    return

                i = i % len(pages)

                await message.edit(embed=pages[i])
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
        await message.clear_reactions()
