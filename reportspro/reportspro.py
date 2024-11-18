from redbot.core import commands, Config, checks
import discord
from datetime import datetime, timezone
import os
import tempfile
import asyncio
from collections import Counter
import random
import string

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
        embed = discord.Embed(
            title="Reports Channel Set",
            description=f"Reports channel set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @reportset.command(name="view")
    async def view_settings(self, ctx):
        """View the current settings for the guild."""
        reports_channel_id = await self.config.guild(ctx.guild).reports_channel()
        reports_channel = ctx.guild.get_channel(reports_channel_id)
        channel_mention = reports_channel.mention if reports_channel else "Not Set"
        
        embed = discord.Embed(title="Current reporting settings", color=discord.Color.from_rgb(255, 255, 254))
        embed.add_field(name="Log channel", value=channel_mention, inline=False)
        
        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission Error",
                description="I do not have permission to send messages in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="report")
    async def report_user(self, ctx, member: discord.Member):
        """Report a user for inappropriate behavior."""
        reports_channel_id = await self.config.guild(ctx.guild).reports_channel()
        if not reports_channel_id:
            embed = discord.Embed(
                title="Error",
                description="Reports channel is not set. Please contact an admin.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        reports_channel = ctx.guild.get_channel(reports_channel_id)
        if not reports_channel:
            embed = discord.Embed(
                title="Error",
                description="Reports channel is not accessible. Please contact an admin.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Create an embed with report types
        report_embed = discord.Embed(
            title=f"Report a user to the moderators of {ctx.guild.name}",
            color=discord.Color.from_rgb(255, 69, 69),
            description=f"**You're reporting {member.mention} ({member.id})**\n\n"
                        f"Please select a reason for the report from the dropdown below."
        )

        # Define report reasons with descriptions and emojis
        report_reasons = [
            ("Harassment", "Unwanted behavior that causes distress or discomfort."),
            ("Spam", "Repeated or irrelevant messages disrupting the chat."),
            ("Advertising", "Unwanted or non-consensual advertising or promotion."),
            ("Inappropriate Content", "Content that is offensive or not suitable for the community."),
            ("Impersonation", "Pretending to be someone else without permission."),
            ("Hate Speech", "Speech that attacks or discriminates against a group."),
            ("Terms of Service", "Actions that violate Discord's Terms of Service."),
            ("Community Guidelines", "Actions that violate Discord's Community Guidelines."),
            ("Other", "Any other reason not listed but reasonably applicable.")
        ]

        # Create a dropdown menu for report reasons
        class ReportDropdown(discord.ui.Select):
            def __init__(self, config, ctx, member, reports_channel, capture_chat_history):
                self.config = config
                self.ctx = ctx
                self.member = member
                self.reports_channel = reports_channel
                self.capture_chat_history = capture_chat_history
                options = [
                    discord.SelectOption(label=reason, description=description)
                    for reason, description in report_reasons
                ]
                super().__init__(placeholder="Choose a report reason...", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_reason = self.values[0]
                selected_description = next(description for reason, description in report_reasons if reason == selected_reason)
                embed = discord.Embed(
                    title="Report submitted",
                    color=discord.Color.from_rgb(43, 189, 142),
                    description=f"Report submitted for {self.member.mention} with reason: {selected_reason}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

                # Deactivate the dropdown
                self.disabled = True
                await interaction.message.edit(view=self.view)

                # Store the report in the config
                try:
                    reports = await self.config.guild(self.ctx.guild).reports()
                    report_id = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
                    while report_id in reports:
                        report_id = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
                    reports[report_id] = {
                        "reported_user": self.member.id,
                        "reporter": self.ctx.author.id,
                        "reason": selected_reason,
                        "description": selected_description,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await self.config.guild(self.ctx.guild).reports.set(reports)
                except Exception as e:
                    embed = discord.Embed(
                        title="Error",
                        description=f"An error occurred while saving the report: {e}",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Capture chat history
                try:
                    chat_history = await self.capture_chat_history(self.ctx.guild, self.member)
                except Exception as e:
                    embed = discord.Embed(
                        title="Error",
                        description=f"An error occurred while capturing chat history: {e}",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Count existing reports against the user by reason
                reason_counts = Counter(report['reason'] for report in reports.values() if report['reported_user'] == self.member.id)

                # Send the report to the reports channel
                if self.reports_channel:
                    report_message = discord.Embed(
                        title="A user in the server was reported",
                        color=discord.Color.from_rgb(255, 69, 69)
                    )
                    report_message.add_field(name="Report ID", value=report_id, inline=False)
                    report_message.add_field(name="Offender", value=f"{self.member.mention} ({self.member.id})", inline=False)
                    report_message.add_field(name="Reporter", value=self.ctx.author.mention, inline=False)
                    report_message.add_field(name="Reason", value=f"{selected_reason}: {selected_description}", inline=False)
                    report_message.add_field(name="Time", value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:R>", inline=False)
                    
                    # Add a summary of existing report counts by reason
                    if reason_counts:
                        summary = "\n".join(f"**{reason}** x**{count}**" for reason, count in reason_counts.items())
                        report_message.add_field(name="Pre-existing reports", value=summary, inline=False)

                    try:
                        await self.reports_channel.send(embed=report_message)
                        if chat_history:
                            await self.reports_channel.send(file=discord.File(chat_history, filename=f"{self.member.id}_chat_history.txt"))
                            os.remove(chat_history)  # Clean up the file after sending
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Permission Error",
                            description="I do not have permission to send messages in the reports channel.",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    except Exception as e:
                        embed = discord.Embed(
                            title="Error",
                            description=f"An error occurred while sending the report: {e}",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="Error",
                        description="Reports channel is not accessible. Please contact an admin.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)

        # Create a view and add the dropdown
        view = discord.ui.View()
        view.add_item(ReportDropdown(self.config, ctx, member, reports_channel, self.capture_chat_history))

        try:
            await ctx.send(embed=report_embed, view=view, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission Error",
                description="I do not have permission to send messages in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while sending the report embed: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)

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
            except Exception as e:
                print(f"An error occurred while accessing channel {channel.name}: {e}")
                continue
        if chat_history:
            try:
                file_path = tempfile.mktemp(suffix=f"_{member.id}_chat_history.txt")
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write("\n".join(chat_history))
                return file_path
            except Exception as e:
                print(f"An error occurred while writing chat history to file: {e}")
                return None
        return None

    @commands.guild_only()
    @commands.command(name="viewreports")
    @checks.admin_or_permissions()
    async def view_reports(self, ctx, member: discord.Member = None):
        """View all reports in the guild or reports for a specific user."""
        reports = await self.config.guild(ctx.guild).reports()
        if not reports:
            embed = discord.Embed(
                title="No Reports",
                description="There are no reports in this guild.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        # Filter reports for a specific member if provided
        filtered_reports = [
            (report_id, report_info) for report_id, report_info in reports.items()
            if not member or (ctx.guild.get_member(report_info['reported_user']) == member)
        ]

        if not filtered_reports:
            embed = discord.Embed(
                title="No Reports",
                description="There are no reports for the specified user.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        # Create a list of embeds, one for each report
        embeds = []
        for report_id, report_info in filtered_reports:
            reported_user = ctx.guild.get_member(report_info['reported_user'])
            reporter = ctx.guild.get_member(report_info['reporter'])

            embed = discord.Embed(title=f"Report ID: {report_id}", color=discord.Color.from_rgb(255, 255, 254))
            embed.add_field(
                name="Reported User",
                value=reported_user.mention if reported_user else 'Unknown User',
                inline=False
            )
            embed.add_field(
                name="Reported By",
                value=reporter.mention if reporter else 'Unknown Reporter',
                inline=False
            )
            embed.add_field(
                name="Reason",
                value=f"{report_info['reason']}: {report_info.get('description', 'No description available')}",
                inline=False
            )
            embed.add_field(
                name="Timestamp",
                value=f"<t:{int(datetime.fromisoformat(report_info.get('timestamp', '1970-01-01T00:00:00+00:00')).timestamp())}:R>",
                inline=False
            )
            embeds.append(embed)

        # Function to handle pagination
        async def send_paginated_embeds(ctx, embeds):
            current_page = 0
            message = await ctx.send(embed=embeds[current_page])

            # Add reaction controls
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            await message.add_reaction("❌")  # Add close emoji

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                    if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                        current_page += 1
                        await message.edit(embed=embeds[current_page])
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=embeds[current_page])
                    elif str(reaction.emoji) == "❌":
                        await message.delete()
                        break

                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break

        await send_paginated_embeds(ctx, embeds)

    @commands.guild_only()
    @commands.command(name="clearreports")
    @checks.admin_or_permissions(manage_guild=True)
    async def clear_reports(self, ctx):
        """Clear all reports in the guild."""
        await self.config.guild(ctx.guild).reports.set({})
        try:
            embed = discord.Embed(
                title="Reports Cleared",
                description="All reports have been cleared.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission Error",
                description="I do not have permission to send messages in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="cleanupreports")
    @checks.admin_or_permissions(manage_guild=True)
    async def cleanup_reports(self, ctx):
        """Manually clean up old reports."""
        reports = await self.config.guild(ctx.guild).reports()
        updated_reports = {k: v for k, v in reports.items() if self.is_recent(v.get('timestamp'))}
        await self.config.guild(ctx.guild).reports.set(updated_reports)
        embed = discord.Embed(
            title="Reports Cleaned",
            description="Old reports have been cleaned up.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    def is_recent(self, timestamp):
        """Check if a report is recent (within 30 days)."""
        if not timestamp:
            return False
        try:
            report_time = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - report_time).days < 30
        except ValueError:
            return False

    @commands.guild_only()
    @commands.command(name="handlereport")
    @checks.admin_or_permissions(manage_guild=True)
    async def handle_report(self, ctx, report_id: str):
        """Handle a report by its ID."""
        reports = await self.config.guild(ctx.guild).reports()
        report = reports.get(report_id)

        if not report:
            embed = discord.Embed(
                title="Report Not Found",
                description="Report not found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        reported_user = ctx.guild.get_member(report['reported_user'])
        reporter = ctx.guild.get_member(report['reporter'])

        # Create a view for handling the report
        class HandleReportView(discord.ui.View):
            def __init__(self, ctx, report_id, reporter, reported_user):
                super().__init__()
                self.ctx = ctx
                self.report_id = report_id
                self.reporter = reporter
                self.reported_user = reported_user
                self.answers = []

            async def ask_question(self, ctx, question, emoji_meanings):
                embed = discord.Embed(
                    title="Report Handling",
                    description=question,
                    color=discord.Color.blue()
                )
                emoji_list = "\n".join([f"{emoji}: {meaning}" for emoji, meaning in emoji_meanings.items()])
                embed.add_field(name="Options", value=emoji_list, inline=False)
                message = await ctx.send(embed=embed)
                for emoji in emoji_meanings.keys():
                    await message.add_reaction(emoji)
                return message

            async def handle_reaction(self, message, emoji_meanings):
                def check(reaction, user):
                    return user == self.ctx.author and str(reaction.emoji) in emoji_meanings

                try:
                    reaction, _ = await self.ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    return str(reaction.emoji)
                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="Timeout",
                        description="You took too long to respond.",
                        color=discord.Color.red()
                    )
                    await self.ctx.send(embed=embed)
                    return None

            async def handle_report(self):
                # Initial question to confirm investigation
                question = "Have you reviewed and investigated all facts of the matter?"
                emoji_meanings = {"✅": "Yes", "❌": "No"}
                message = await self.ask_question(self.ctx, question, emoji_meanings)
                emoji = await self.handle_reaction(message, emoji_meanings)
                if emoji is None or emoji_meanings[emoji] == "No":
                    embed = discord.Embed(
                        title="Investigation Required",
                        description="Please review all facts before proceeding.",
                        color=discord.Color.orange()
                    )
                    await self.ctx.send(embed=embed)
                    return
                self.answers.append(emoji_meanings[emoji])

                # Question to determine validity of the report
                question = "Do you believe the report, including its evidence and reason, is valid?"
                emoji_meanings = {"✅": "Valid", "❌": "Invalid"}
                message = await self.ask_question(self.ctx, question, emoji_meanings)
                emoji = await self.handle_reaction(message, emoji_meanings)
                if emoji is None or emoji_meanings[emoji] == "Invalid":
                    embed = discord.Embed(
                        title="Report Invalid",
                        description="The report has been deemed invalid. No further action will be taken.",
                        color=discord.Color.orange()
                    )
                    await self.ctx.send(embed=embed)
                    self.answers.append("Invalid")
                    await self.finalize()
                    return
                self.answers.append(emoji_meanings[emoji])

                # Final question to decide action
                question = "What action should be taken against the reported user?"
                emoji_meanings = {"⚠️": "Warning", "⏲️": "Timeout", "🔨": "Ban"}
                message = await self.ask_question(self.ctx, question, emoji_meanings)
                emoji = await self.handle_reaction(message, emoji_meanings)
                if emoji is None:
                    return
                self.answers.append(emoji_meanings[emoji])

                await self.finalize()

            async def finalize(self):
                action = self.answers[2] if len(self.answers) > 2 else "No action"
                if action == "Warning" and self.reported_user:
                    try:
                        await self.reported_user.send("You have received a warning due to a report against you.")
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Warning Error",
                            description="Could not send a warning to the reported user.",
                            color=discord.Color.red()
                        )
                        await self.ctx.send(embed=embed)
                elif action == "Timeout" and self.reported_user:
                    try:
                        await self.reported_user.timeout(duration=86400)  # Timeout for 24 hours
                        embed = discord.Embed(
                            title="User Timed Out",
                            description=f"{self.reported_user.mention} has been timed out for 24 hours.",
                            color=discord.Color.green()
                        )
                        await self.ctx.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Timeout Error",
                            description="Could not timeout the reported user.",
                            color=discord.Color.red()
                        )
                        await self.ctx.send(embed=embed)
                elif action == "Ban" and self.reported_user:
                    try:
                        await self.reported_user.ban(reason="Report handled and deemed valid.")
                        embed = discord.Embed(
                            title="User Banned",
                            description=f"{self.reported_user.mention} has been banned.",
                            color=discord.Color.green()
                        )
                        await self.ctx.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Ban Error",
                            description="Could not ban the reported user.",
                            color=discord.Color.red()
                        )
                        await self.ctx.send(embed=embed)

                if self.reporter:
                    try:
                        embed = discord.Embed(
                            title="An update on your earlier report",
                            description=(
                                f"The report you submitted earlier has been reviewed by a staff member. "
                                f"After careful consideration, the report was deemed {self.answers[1]}. "
                                f"As a result, the following action has been taken against the reported user: {action}."
                            ),
                            color=discord.Color.blue()
                        )
                        await self.reporter.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="DM Error",
                            description="Could not send a DM to the reporter.",
                            color=discord.Color.red()
                        )
                        await self.ctx.send(embed=embed)

                embed = discord.Embed(
                    title="Report Handled",
                    description=f"Report {self.report_id} has been handled. Action: {action}.",
                    color=discord.Color.green()
                )
                await self.ctx.send(embed=embed)
                self.stop()

        view = HandleReportView(ctx, report_id, reporter, reported_user)
        await view.handle_report()
