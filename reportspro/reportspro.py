from redbot.core import commands, Config, checks
import discord

class ReportsPro(commands.Cog):
    """Cog to handle global user reports"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "reports_channel": None,
            "reports": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.command(name="setreportchannel")
    @checks.admin_or_permissions(manage_guild=True)
    async def set_report_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where reports will be sent."""
        await self.config.guild(ctx.guild).reports_channel.set(channel.id)
        await ctx.send(f"Reports channel set to {channel.mention}")

    @commands.guild_only()
    @commands.command(name="report")
    async def report_user(self, ctx, member: discord.Member, *, reason: str):
        """Report a user for inappropriate behavior."""
        reports_channel_id = await self.config.guild(ctx.guild).reports_channel()
        if not reports_channel_id:
            await ctx.send("Reports channel is not set. Please contact an admin.")
            return

        reports_channel = ctx.guild.get_channel(reports_channel_id)
        if not reports_channel:
            await ctx.send("Reports channel is not accessible. Please contact an admin.")
            return

        report_embed = discord.Embed(
            title="New User Report",
            color=discord.Color.red(),
            description=f"**Reported User:** {member.mention} ({member.id})\n"
                        f"**Reported By:** {ctx.author.mention} ({ctx.author.id})\n"
                        f"**Reason:** {reason}"
        )
        await reports_channel.send(embed=report_embed)
        await ctx.send("Thank you for your report. The moderators have been notified.")

        # Store the report in the config
        reports = await self.config.guild(ctx.guild).reports()
        report_id = len(reports) + 1
        reports[report_id] = {
            "reported_user": member.id,  # Store user ID instead of mention
            "reporter": ctx.author.id,   # Store reporter ID instead of mention
            "reason": reason
        }
        await self.config.guild(ctx.guild).reports.set(reports)

    @commands.guild_only()
    @commands.command(name="viewreports")
    @checks.admin_or_permissions(manage_guild=True)
    async def view_reports(self, ctx):
        """View all reports in the guild."""
        reports = await self.config.guild(ctx.guild).reports()
        if not reports:
            await ctx.send("There are no reports in this guild.")
            return

        embed = discord.Embed(title="User Reports", color=discord.Color.blue())
        for report_id, report_info in reports.items():
            reported_user = ctx.guild.get_member(report_info['reported_user'])
            reporter = ctx.guild.get_member(report_info['reporter'])
            embed.add_field(
                name=f"Report ID: {report_id}",
                value=f"**Reported User:** {reported_user.mention if reported_user else 'Unknown User'}\n"
                      f"**Reported By:** {reporter.mention if reporter else 'Unknown Reporter'}\n"
                      f"**Reason:** {report_info['reason']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="clearreports")
    @checks.admin_or_permissions(manage_guild=True)
    async def clear_reports(self, ctx):
        """Clear all reports in the guild."""
        await self.config.guild(ctx.guild).reports.set({})
        await ctx.send("All reports have been cleared.")
