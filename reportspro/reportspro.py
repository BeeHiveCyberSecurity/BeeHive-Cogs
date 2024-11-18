from redbot.core import commands, Config, checks
import discord
from datetime import datetime, timezone
import os
import tempfile
import asyncio

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
        
        embed = discord.Embed(title="Current reporting settings", color=discord.Color.from_rgb(255, 255, 254))
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
            title="Report a user to moderators",
            color=discord.Color.from_rgb(255, 69, 69),
            description=f"**You're reporting {member.mention} ({member.id})**\n"
                        f"Please select a reason for the report from the dropdown below."
        )

        # Define report reasons with descriptions and emojis
        report_reasons = [
            ("Harassment", "Unwanted behavior that causes distress or discomfort."),
            ("Spam", "Repeated or irrelevant messages disrupting the chat."),
            ("Inappropriate Content", "Content that is offensive or not suitable for the community."),
            ("Impersonation", "Pretending to be someone else without permission."),
            ("Hate Speech", "Speech that attacks or discriminates against a group."),
            ("Discord ToS Violation", "Actions that violate Discord's Terms of Service."),
            ("Discord Community Guidelines Violation", "Actions that violate Discord's Community Guidelines."),
            ("Other", "Any other reason not listed.")
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
                try:
                    chat_history = await self.capture_chat_history(self.ctx.guild, self.member)
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred while capturing chat history: {e}", ephemeral=True)
                    return

                # Send the report to the reports channel
                if self.reports_channel:
                    report_message = discord.Embed(
                        title="New User Report",
                        color=discord.Color.from_rgb(255, 69, 69)
                    )
                    report_message.add_field(name="Reported User", value=f"{self.member.mention} ({self.member.id})", inline=False)
                    report_message.add_field(name="Reported By", value=self.ctx.author.mention, inline=False)
                    report_message.add_field(name="Reason", value=selected_reason, inline=False)
                    report_message.add_field(name="Timestamp", value=datetime.now(timezone.utc).isoformat(), inline=False)
                    try:
                        await self.reports_channel.send(embed=report_message)
                        if chat_history:
                            await self.reports_channel.send(file=discord.File(chat_history, filename=f"{self.member.id}_chat_history.txt"))
                            os.remove(chat_history)  # Clean up the file after sending
                    except discord.Forbidden:
                        await interaction.response.send_message("I do not have permission to send messages in the reports channel.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"An error occurred while sending the report: {e}", ephemeral=True)
                else:
                    await interaction.response.send_message("Reports channel is not accessible. Please contact an admin.", ephemeral=True)

        # Create a view and add the dropdown
        view = discord.ui.View()
        view.add_item(ReportDropdown(self.config, ctx, member, reports_channel, self.capture_chat_history))

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
            await ctx.send("There are no reports in this guild.")
            return

        # Filter reports for a specific member if provided
        filtered_reports = [
            (report_id, report_info) for report_id, report_info in reports.items()
            if not member or (ctx.guild.get_member(report_info['reported_user']) == member)
        ]

        if not filtered_reports:
            await ctx.send("There are no reports for the specified user.")
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
                value=report_info['reason'],
                inline=False
            )
            embed.add_field(
                name="Timestamp",
                value=report_info.get('timestamp', 'Unknown'),
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

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                    if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                        current_page += 1
                        await message.edit(embed=embeds[current_page])
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=embeds[current_page])

                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break

        await send_paginated_embeds(ctx, embeds)

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
