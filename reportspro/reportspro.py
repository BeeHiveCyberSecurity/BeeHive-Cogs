from redbot.core import commands, Config, checks
import discord
from datetime import datetime, timezone
import os
import tempfile

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
    @commands.group(name="reportset", invoke_without_command=True)
    @checks.admin_or_permissions()
    async def reportset(self, ctx):
        """Group command for report settings."""
        await ctx.send_help(ctx.command)

    @reportset.command(name="channel")
    async def set_report_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where reports will be sent."""
        await self.config.guild(ctx.guild).reports_channel.set(channel.id)
        await ctx.send(f"Reports channel set to {channel.mention}")

    @reportset.command(name="view")
    async def view_settings(self, ctx):
        """View the current settings for the guild."""
        reports_channel_id = await self.config.guild(ctx.guild).reports_channel()
        reports_channel = ctx.guild.get_channel(reports_channel_id)
        channel_mention = reports_channel.mention if reports_channel else "Not Set"
        
        embed = discord.Embed(title="Current reporting settings", color=discord.Color.from_rgb(43, 189, 142))
        embed.add_field(name="Log channel", value=channel_mention, inline=False)
        
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
            await ctx.send("Reports channel is not set. Please contact an admin.", ephemeral=True)
            return

        reports_channel = ctx.guild.get_channel(reports_channel_id)
        if not reports_channel:
            await ctx.send("Reports channel is not accessible. Please contact an admin.", ephemeral=True)
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
                embed = discord.Embed(
                    title="Report submitted",
                    color=discord.Color.from_rgb(43, 189, 142),
                    description=f"Report submitted for {self.member.mention} with reason: {selected_reason}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

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
                    await interaction.response.send_message(f"An error occurred while saving the report: {e}", ephemeral=True)
                    return

                # Capture chat history
                chat_history = await self.capture_chat_history(self.ctx.guild, self.member)

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
                        if chat_history:
                            await self.reports_channel.send(file=discord.File(chat_history, filename=f"{self.member.id}_chat_history.txt"))
                            os.remove(chat_history)  # Clean up the file after sending
                    except discord.Forbidden:
                        await interaction.response.send_message("I do not have permission to send messages in the reports channel.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"An error occurred while sending the report: {e}", ephemeral=True)

        # Create a view and add the dropdown
        view = discord.ui.View()
        view.add_item(ReportDropdown(self.config, ctx, member, reports_channel))

        try:
            await ctx.send(embed=report_embed, view=view, ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in this channel.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"An error occurred while sending the report embed: {e}", ephemeral=True)

    async def capture_chat_history(self, guild, member):
        """Capture the chat history of a member across all channels."""
        chat_history = []
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=100, oldest_first=False):
                    if message.author == member:
                        chat_history.append(f"[{message.created_at}] {message.author}: {message.content}")
            except discord.Forbidden:
                continue
        if chat_history:
            file_path = tempfile.mktemp(suffix=f"_{member.id}_chat_history.txt")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(chat_history))
            return file_path
        return None

    @commands.guild_only()
    @commands.command(name="viewreports")
    @checks.admin_or_permissions()
    async def view_reports(self, ctx, member: discord.Member = None):
        """View all reports in the guild or reports for a specific user."""
        reports = await self.config.guild(ctx.guild).reports()
        if not reports:
            await ctx.send("There are no reports in this guild.")
            return

        embed = discord.Embed(title="User Reports", color=discord.Color.blue())
        for report_id, report_info in reports.items():
            reported_user = ctx.guild.get_member(report_info['reported_user'])
            reporter = ctx.guild.get_member(report_info['reporter'])

            if member and (not reported_user or reported_user != member):
                continue

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
