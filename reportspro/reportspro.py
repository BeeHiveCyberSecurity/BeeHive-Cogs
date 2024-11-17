from redbot.core import commands, Config, checks
import discord
from discord.ext import tasks
from datetime import datetime, timezone

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
        self.cleanup_reports.start()

    def cog_unload(self):
        self.cleanup_reports.cancel()

    @commands.guild_only()
    @commands.command(name="setreportchannel")
    @checks.admin_or_permissions()
    async def set_report_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where reports will be sent."""
        await self.config.guild(ctx.guild).reports_channel.set(channel.id)
        await ctx.send(f"Reports channel set to {channel.mention}")

    @commands.guild_only()
    @commands.command(name="viewsettings")
    @checks.admin_or_permissions()
    async def view_settings(self, ctx):
        """View the current settings for the guild."""
        reports_channel_id = await self.config.guild(ctx.guild).reports_channel()
        reports_channel = ctx.guild.get_channel(reports_channel_id)
        channel_mention = reports_channel.mention if reports_channel else "Not Set"
        
        embed = discord.Embed(title="Current Settings", color=discord.Color.green())
        embed.add_field(name="Reports Channel", value=channel_mention, inline=False)
        
        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in this channel.")

    @commands.guild_only()
    @commands.command(name="report")
    async def report_user(self, ctx, member: discord.Member):
        """Report a user for inappropriate behavior."""
        reports_channel_id = await self.config.guild(ctx.guild).reports_channel()
        if not reports_channel_id:
            await ctx.send("Reports channel is not set. Please contact an admin.")
            return

        reports_channel = ctx.guild.get_channel(reports_channel_id)
        if not reports_channel:
            await ctx.send("Reports channel is not accessible. Please contact an admin.")
            return

        # Create an embed with report types
        report_embed = discord.Embed(
            title="Report User",
            color=discord.Color.red(),
            description=f"**Reported User:** {member.mention} ({member.id})\n"
                        f"Please select a reason for the report from the dropdown below."
        )

        # Define report reasons
        report_reasons = [
            "Harassment",
            "Spam",
            "Inappropriate Content",
            "Other"
        ]

        # Create a dropdown menu for report reasons
        class ReportDropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=reason, description=f"Report for {reason}")
                    for reason in report_reasons
                ]
                super().__init__(placeholder="Choose a report reason...", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_reason = self.values[0]
                await interaction.response.send_message(f"Report submitted for {member.mention} with reason: {selected_reason}")

                # Store the report in the config
                reports = await self.config.guild(ctx.guild).reports()
                report_id = len(reports) + 1
                reports[report_id] = {
                    "reported_user": member.id,
                    "reporter": ctx.author.id,
                    "reason": selected_reason,
                    "timestamp": ctx.message.created_at.replace(tzinfo=timezone.utc).isoformat()
                }
                await self.config.guild(ctx.guild).reports.set(reports)

                # Send the report to the reports channel
                if reports_channel:
                    report_message = discord.Embed(
                        title="New User Report",
                        color=discord.Color.red(),
                        description=f"**Reported User:** {member.mention} ({member.id})\n"
                                    f"**Reported By:** {ctx.author.mention}\n"
                                    f"**Reason:** {selected_reason}\n"
                                    f"**Timestamp:** {ctx.message.created_at.replace(tzinfo=timezone.utc).isoformat()}"
                    )
                    try:
                        await reports_channel.send(embed=report_message)
                    except discord.Forbidden:
                        await ctx.send("I do not have permission to send messages in the reports channel.")

        # Create a view and add the dropdown
        view = discord.ui.View()
        view.add_item(ReportDropdown())

        try:
            await ctx.send(embed=report_embed, view=view)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in this channel.")

    @commands.guild_only()
    @commands.command(name="viewreports")
    @checks.admin_or_permissions()
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
                      f"**Reason:** {report_info['reason']}\n"
                      f"**Timestamp:** {report_info.get('timestamp', 'Unknown')}",
                inline=False
            )
        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in this channel.")

    @commands.guild_only()
    @commands.command(name="clearreports")
    @checks.admin_or_permissions(manage_guild=True)
    async def clear_reports(self, ctx):
        """Clear all reports in the guild."""
        await self.config.guild(ctx.guild).reports.set({})
        try:
            await ctx.send("All reports have been cleared.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in this channel.")

    @tasks.loop(hours=24)
    async def cleanup_reports(self):
        """Automatically clean up old reports every 24 hours."""
        for guild in self.bot.guilds:
            reports = await self.config.guild(guild).reports()
            updated_reports = {k: v for k, v in reports.items() if self.is_recent(v.get('timestamp'))}
            await self.config.guild(guild).reports.set(updated_reports)

    def is_recent(self, timestamp):
        """Check if a report is recent (within 30 days)."""
        if not timestamp:
            return False
        try:
            report_time = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - report_time).days < 30
        except ValueError:
            return False
