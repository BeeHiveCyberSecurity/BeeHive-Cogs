from redbot.core import commands, Config, checks
import discord
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

        # Define report reasons with descriptions
        report_reasons = [
            ("Harassment", "Unwanted behavior that causes distress or discomfort."),
            ("Spam", "Repeated or irrelevant messages disrupting the chat."),
            ("Inappropriate Content", "Content that is offensive or not suitable for the community."),
            ("Cheating", "Unfair advantage or breaking the rules of the game."),
            ("Impersonation", "Pretending to be someone else without permission."),
            ("Hate Speech", "Speech that attacks or discriminates against a group."),
            ("Discord ToS Violation", "Actions that violate Discord's Terms of Service."),
            ("Discord Community Guidelines Violation", "Actions that violate Discord's Community Guidelines."),
            ("Other", "Any other reason not listed.")
        ]

        # Create a dropdown menu for report reasons
        class ReportDropdown(discord.ui.Select):
            def __init__(self, config, ctx, member, reports_channel):
                self.config = config
                self.ctx = ctx
                self.member = member
                self.reports_channel = reports_channel
                options = [
                    discord.SelectOption(label=reason, description=description)
                    for reason, description in report_reasons
                ]
                super().__init__(placeholder="Choose a report reason...", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_reason = self.values[0]
                await interaction.response.send_message(f"Report submitted for {self.member.mention} with reason: {selected_reason}")

                # Store the report in the config
                try:
                    reports = await self.config.guild(self.ctx.guild).reports()
                    report_id = len(reports) + 1
                    reports[str(report_id)] = {
                        "reported_user": self.member.id,
                        "reporter": self.ctx.author.id,
                        "reason": selected_reason,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await self.config.guild(self.ctx.guild).reports.set(reports)
                except Exception as e:
                    await self.ctx.send(f"An error occurred while saving the report: {e}")
                    return

                # Send the report to the reports channel
                if self.reports_channel:
                    report_message = discord.Embed(
                        title="New User Report",
                        color=discord.Color.red(),
                        description=f"**Reported User:** {self.member.mention} ({self.member.id})\n"
                                    f"**Reported By:** {self.ctx.author.mention}\n"
                                    f"**Reason:** {selected_reason}\n"
                                    f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}"
                    )
                    try:
                        await self.reports_channel.send(embed=report_message)
                    except discord.Forbidden:
                        await self.ctx.send("I do not have permission to send messages in the reports channel.")
                    except Exception as e:
                        await self.ctx.send(f"An error occurred while sending the report: {e}")

        # Create a view and add the dropdown
        view = discord.ui.View()
        view.add_item(ReportDropdown(self.config, ctx, member, reports_channel))

        try:
            await ctx.send(embed=report_embed, view=view)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in this channel.")
        except Exception as e:
            await ctx.send(f"An error occurred while sending the report embed: {e}")

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

    @commands.guild_only()
    @commands.command(name="cleanupreports")
    @checks.admin_or_permissions(manage_guild=True)
    async def cleanup_reports(self, ctx):
        """Manually clean up old reports."""
        reports = await self.config.guild(ctx.guild).reports()
        updated_reports = {k: v for k, v in reports.items() if self.is_recent(v.get('timestamp'))}
        await self.config.guild(ctx.guild).reports.set(updated_reports)
        await ctx.send("Old reports have been cleaned up.")

    def is_recent(self, timestamp):
        """Check if a report is recent (within 30 days)."""
        if not timestamp:
            return False
        try:
            report_time = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - report_time).days < 30
        except ValueError:
            return False
