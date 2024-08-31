import stripe  # type: ignore
from redbot.core import Config, commands, checks  # type: ignore
from redbot.core.bot import Red  # type: ignore
import discord  # type: ignore
import asyncio
from datetime import datetime, timedelta

class StripeIdentity(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_global(
            stripe_api_key="",
            verification_channel=None,
            age_verified_role=None,
            id_verified_role=None,
            pending_verification_sessions={}
        )

    async def initialize(self):
        api_key = await self.bot.get_shared_api_tokens("stripe")
        stripe.api_key = api_key.get("api_key")
        self.verification_channel_id = await self.config.verification_channel()
        self.age_verified_role_id = await self.config.age_verified_role()
        self.id_verified_role_id = await self.config.id_verified_role()

    async def send_embed(self, ctx, description, color):
        embed = discord.Embed(description=description, color=color)
        await ctx.send(embed=embed)

    @commands.command(name="setverificationchannel")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def set_verification_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Set the channel where verification results will be sent.
        """
        if not channel:
            await self.send_embed(ctx, ":x: **Invalid channel provided.** Please mention a valid text channel.", discord.Color.red())
            return
        
        await self.config.verification_channel.set(channel.id)
        await self.send_embed(ctx, f"Verification results will now be sent to {channel.mention}.", discord.Color(0x2BBD8E))

    @commands.command(name="setageverifiedrole")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def set_age_verified_role(self, ctx: commands.Context, role: discord.Role):
        """
        Set the role to give to users who are verified as 18 or older.
        """
        if not role:
            await self.send_embed(ctx, ":x: **Invalid role provided.** Please mention a valid role.", discord.Color.red())
            return
        
        await self.config.age_verified_role.set(role.id)
        await self.send_embed(ctx, f"Role for age verified users set to {role.name}.", discord.Color(0x2BBD8E))

    @commands.command(name="setidverifiedrole")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def set_id_verified_role(self, ctx: commands.Context, role: discord.Role):
        """
        Set the role to give to users who have been completely ID verified.
        """
        if not role:
            await self.send_embed(ctx, ":x: **Invalid role provided.** Please mention a valid role.", discord.Color.red())
            return
        
        await self.config.id_verified_role.set(role.id)
        await self.send_embed(ctx, f"Role for ID verified users set to {role.name}.", discord.Color(0x2BBD8E))

    @commands.command(name="cancelverification")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def cancel_verification(self, ctx: commands.Context, user: discord.Member):
        """
        Cancel a pending verification session for a user and remove it from the list of sessions.
        """
        session_id = await self.config.pending_verification_sessions.get_raw(str(user.id), default=None)
        if session_id:
            try:
                verification_session = stripe.identity.VerificationSession.retrieve(session_id)
                if verification_session.status in ["requires_input", "processing"]:
                    stripe.identity.VerificationSession.cancel(session_id)
                    await self.config.pending_verification_sessions.clear_raw(str(user.id))
                    await self.send_embed(ctx, f"Verification session for {user.display_name} has been canceled and removed.", discord.Color(0x2BBD8E))
                else:
                    await self.send_embed(ctx, f"Verification session for {user.display_name} cannot be canceled as it is already {verification_session.status}.", discord.Color.orange())
            except stripe.error.StripeError as e:
                await self.send_embed(ctx, f"Failed to cancel the verification session: {e.user_message}", discord.Color.red())
            except Exception as e:
                await self.send_embed(ctx, f"An unexpected error occurred: {str(e)}", discord.Color.red())
        else:
            await self.send_embed(ctx, f"No pending verification session found for {user.display_name}.", discord.Color.orange())

    @commands.is_owner()
    @commands.guild_only()
    @commands.command(name="bypassverification")
    async def bypass_verification(self, ctx: commands.Context, user: discord.Member):
        """
        Bypass the verification process for a user.
        """
        await self.config.pending_verification_sessions.clear_raw(str(user.id))
        
        age_verified_role_id = await self.config.age_verified_role()
        id_verified_role_id = await self.config.id_verified_role()
        
        # Check if the roles exist before attempting to add them
        age_verified_role = ctx.guild.get_role(age_verified_role_id) if age_verified_role_id else None
        id_verified_role = ctx.guild.get_role(id_verified_role_id) if id_verified_role_id else None
        
        if age_verified_role:
            await user.add_roles(age_verified_role, reason="Bypassed verification")
        if id_verified_role:
            await user.add_roles(id_verified_role, reason="Bypassed verification")

        # Cancel the verification countdown
        if hasattr(self, 'verification_tasks') and str(user.id) in self.verification_tasks:
            self.verification_tasks[str(user.id)].cancel()
            del self.verification_tasks[str(user.id)]

        await self.send_embed(ctx, f"{user.display_name}'s verification has been bypassed.", discord.Color(0x2BBD8E))

    @commands.command(name="agecheck")
    @commands.guild_only()
    @checks.mod_or_permissions()
    async def age_check(self, ctx: commands.Context, user: discord.Member):
        """
        Perform an age check on a user using Stripe Identity.
        """
        await ctx.message.delete()
        await self.send_embed(ctx, "**Attempting to create verification session, please wait...**", discord.Color(0x2BBD8E))
        try:
            verification_session = stripe.identity.VerificationSession.create(
                type='document',
                metadata={
                    'requester_id': str(ctx.author.id),
                    'target_id': str(user.id),
                    'discord_server_id': str(ctx.guild.id),
                    'command_used': 'agecheck'
                },
                options={
                    'document': {
                        'allowed_types': ['driving_license', 'passport', 'id_card'],
                        'require_id_number': False,
                        'require_live_capture': True,
                        'require_matching_selfie': True,
                    },
                }
            )
            await self.config.pending_verification_sessions.set_raw(str(user.id), value=verification_session.id)
            dm_embed = discord.Embed(
                title="Age verification requested",
                description=(
                    f"Hello {user.mention},\n\n"
                    f"To enhance safety and security within our community, **{ctx.guild.name}** requires you to verify your age, and link it to your Discord account. \n\n"
                    "> This procedure involves the confirmation of your name and age using a government-issued ID and biometric verification.\n"
                    "### Please ensure you have one of the following documents:\n- **State ID**\n- **Driver's License**\n- **Driver's Permit**\n- **Passport**\n"
                    "### You will also need to:\n- **Provide a valid email address**\n- **Take a series of selfies in a well-lit area**\n- **Submit the identity document mentioned above for biometric matching and analysis**\n\n"
                    "Upon completing the verification, your personal information will be handled according to the following legal agreements:\n- **[BeeHive Terms of Service](<https://www.beehive.systems/tos>)**\n- **[BeeHive Privacy Policy](https://www.beehive.systems/privacy)**\n- **[Stripe Privacy Policy](https://stripe.com/privacy)**\n- **[Stripe Consumer Terms of Service](https://stripe.com/legal/consumer)**\n\n"
                    "Should you choose not to provide your personal information, you can opt out of the verification process by selecting the option below. This action will result in your immediate removal from the server. If no action is taken within **15 minutes**, you will be automatically removed from the server."
                ),
                color=discord.Color(0xff4545)
            )
            dm_embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/id-card.png")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Start verification", url=f"{verification_session.url}", style=discord.ButtonStyle.link, emoji="<:globe:1196807971674533968>"))
            
            decline_button = discord.ui.Button(label="Decline verification", style=discord.ButtonStyle.danger)
            async def decline_verification(interaction: discord.Interaction):
                if interaction.user.id == user.id:
                    await interaction.response.send_message(f"You have declined the verification.", ephemeral=True)
                    await self.config.pending_verification_sessions.clear_raw(str(user.id))
            decline_button.callback = decline_verification
            view.add_item(decline_button)
            try:
                dm_message = await user.send(embed=dm_embed, view=view)
            except discord.Forbidden:
                await self.send_embed(ctx, f":x: **Failed to send DM to {user.display_name}**. They might have DMs disabled.", discord.Color(0xff4545))
                return

            await self.send_embed(ctx, f":white_check_mark: **`AGE` verification session created for {user.mention}. They've been sent instructions on how to continue.**", discord.Color(0x2BBD8E))

            async def check_verification_status(session_id):
                session = stripe.identity.VerificationSession.retrieve(session_id)
                if session.status == 'requires_input' and session.last_error:
                    for event in session.last_error:
                        if event.code in ['consent_declined', 'device_unsupported', 'under_supported_age', 'phone_otp_declined', 'email_verification_declined']:
                            return event.code, session
                return session.status == 'verified', session

            for _ in range(15):  # Check every minute for 15 minutes
                await asyncio.sleep(60)
                status, session = await check_verification_status(verification_session.id)
                if isinstance(status, str) and status in ['consent_declined', 'device_unsupported', 'under_supported_age', 'phone_otp_declined', 'email_verification_declined']:
                    await self.send_embed(ctx, f":x: **Verification failed due to `{status.replace('_', ' ')}`**", discord.Color(0xff4545))
                    await user.send(f":x: **Verification failed due to `{status.replace('_', ' ')}`**")
                    break
                elif status == 'abandoned':
                    await self.send_embed(ctx, f":x: **Verification session for {user.display_name} has been abandoned.**", discord.Color(0xff4545))
                    await user.send(f":x: **Verification session for {user.display_name} has been abandoned.**")
                    break
                elif status == 'verified':
                    verification_channel = self.bot.get_channel(self.verification_channel_id)
                    if verification_channel:
                        dob = datetime.fromisoformat(session.last_verification_report.document.dob)
                        age = (datetime.utcnow() - dob).days // 365
                        if age < 18:
                            dm_embed = discord.Embed(
                                title="Underage user detected",
                                description=(
                                    "You are under 18 and cannot be verified.\n\n"
                                    "You may return once you are 18 years of age or older...\n\n"
                                    "**If you have any questions, please contact a staff member.**"
                                ),
                                color=discord.Color(0xff4545)
                            )
                            await user.send(embed=dm_embed)
                        else:
                            age_verified_role = ctx.guild.get_role(self.age_verified_role_id)
                            if age_verified_role:
                                await user.add_roles(age_verified_role, reason="Age verified as 18+")
                            result_embed = discord.Embed(title="Age Verification Result", color=discord.Color(0x2BBD8E))
                            result_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                            result_embed.add_field(name="Age", value=str(age), inline=False)
                            await verification_channel.send(embed=result_embed)
                    else:
                        result_embed = discord.Embed(title="Age Verification Result", color=discord.Color(0x2BBD8E))
                        result_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                        result_embed.add_field(name="Age", value=str(age), inline=False)
                        await ctx.send(embed=result_embed)
                    break
            else:
                dm_embed = discord.Embed(
                    title="Verification failure",
                    description=f"Verification was not completed in time. Please try again.",
                    color=discord.Color(0xff4545)
                )
                await user.send(embed=dm_embed)
                await self.send_embed(ctx, f":x: **Verification for {user.display_name} was not completed in time.**", discord.Color(0xff4545))
                stripe.identity.VerificationSession.cancel(verification_session.id)  # Cancel the session if not completed
            await self.config.pending_verification_sessions.clear_raw(str(user.id))
        except stripe.error.StripeError as e:
            await self.send_embed(ctx, f":x: **Failed to create a verification session**\n`{e.user_message}`", discord.Color(0xff4545))
        except discord.HTTPException as e:
            await self.send_embed(ctx, f":x: **Failed to send DM to {user.display_name}**\n`{e.text}`", discord.Color(0xff4545))
        except Exception as e:
            await self.send_embed(ctx, f":x: **An unexpected error occurred**\n`{str(e)}`", discord.Color(0xff4545))

    @commands.command(name="identitycheck")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def identity_check(self, ctx: commands.Context, user: discord.Member):
        """
        Perform a biometric verification of a Discord user's identity.
        """
        await ctx.message.delete()
        await self.send_embed(ctx, "**Opening session, please wait...**", discord.Color(0x2BBD8E))
        try:
            verification_session = stripe.identity.VerificationSession.create(
                type='document',
                metadata={
                    'requester_id': str(ctx.author.id),
                    'target_id': str(user.id),
                    'discord_server_id': str(ctx.guild.id),
                    'command_used': 'identitycheck'
                },
                options={
                    'document': {
                        'allowed_types': ['driving_license', 'passport', 'id_card'],
                        'require_id_number': False,
                        'require_live_capture': True,
                        'require_matching_selfie': True,
                    },
                }
            )
            await self.config.pending_verification_sessions.set_raw(str(user.id), value=verification_session.id)
            dm_embed = discord.Embed(
                title="Identity verification required",
                description=(
                    f"Hello {user.mention},\n\n"
                    f"To enhance safety and security within our community, **{ctx.guild.name}** requires you to verify your identity, and link it to your Discord account. \n\n"
                    "> This procedure involves the confirmation of your identity using a government-issued ID and biometric verification.\n"
                    "### Please ensure you have one of the following documents:\n- **State ID**\n- **Driver's License**\n- **Driver's Permit**\n- **Passport**\n"
                    "### You will also need to:\n- **Provide a valid email address**\n- **Take a series of selfies in a well-lit area**\n- **Submit the identity document mentioned above for biometric matching and analysis**\n\n"
                    "Upon completing the verification, your personal information will be handled according to the following legal agreements:\n- **[BeeHive Terms of Service](<https://www.beehive.systems/tos>)**\n- **[BeeHive Privacy Policy](https://www.beehive.systems/privacy)**\n- **[Stripe Privacy Policy](https://stripe.com/privacy)**\n- **[Stripe Consumer Terms of Service](https://stripe.com/legal/consumer)**\n\n"
                    "Should you choose not to provide your personal information, you can opt out of the verification process by selecting the option below. This action will result in your immediate removal from the server. If no action is taken within **15 minutes**, you will be automatically removed from the server."
                ),
                color=discord.Color(0xff4545)
            )
            dm_embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/id-card.png")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Start verification", url=f"{verification_session.url}", style=discord.ButtonStyle.link, emoji="<:globe:1196807971674533968>"))
            decline_button = discord.ui.Button(label="Decline verification", style=discord.ButtonStyle.danger)
            async def decline_verification(interaction: discord.Interaction):
                if interaction.user.id == user.id:
                    await interaction.response.send_message(f"You have declined the verification and have been banned from {ctx.guild.name}.", ephemeral=True)
                    await ctx.guild.ban(user, reason="User declined identity verification")
                    await self.config.pending_verification_sessions.clear_raw(str(user.id))
            decline_button.callback = decline_verification
            view.add_item(decline_button)
            try:
                dm_message = await user.send(embed=dm_embed, view=view)
            except discord.Forbidden:
                await self.send_embed(ctx, f":x: **Failed to send DM to {user.display_name}**. They might have DMs disabled.", discord.Color(0xff4545))
                return

            await self.send_embed(ctx, f"A verification session is now open. I've sent {user.mention} a message with details on how to continue.\n**If they don't verify, I'll ban them within 15 minutes.**", discord.Color(0x2BBD8E))

            async def check_verification_status(session_id):
                if await self.config.pending_verification_sessions.get_raw(str(user.id), default=None) != session_id:
                    return 'cancelled', None
                session = stripe.identity.VerificationSession.retrieve(session_id)
                if session.status == 'requires_input' and session.last_error:
                    for event in session.last_error:
                        if event['code'] in ['consent_declined', 'device_unsupported', 'under_supported_age', 'phone_otp_declined', 'email_verification_declined']:
                            return event['code'], session
                return session.status, session

            for _ in range(15):  # Check every minute for 15 minutes
                await asyncio.sleep(60)
                status, session = await check_verification_status(verification_session.id)
                if status == 'cancelled':
                    await self.send_embed(ctx, f"Identity verification for {user.display_name} has been cancelled.", discord.Color.orange())
                    break
                elif status in ['consent_declined', 'device_unsupported', 'under_supported_age', 'phone_otp_declined', 'email_verification_declined']:
                    await self.send_embed(ctx, f"Identity verification failed due to {status.replace('_', ' ')}.", discord.Color(0xff4545))
                    break
                elif status == 'abandoned':
                    await self.send_embed(ctx, f":x: **Verification session for {user.display_name} has been abandoned.**", discord.Color(0xff4545))
                    break
                elif status == 'verified':
                    id_verified_role = ctx.guild.get_role(self.id_verified_role_id)
                    if id_verified_role:
                        await user.add_roles(id_verified_role, reason="Identity verified")
                    verification_channel = self.bot.get_channel(self.verification_channel_id)
                    result_embed = discord.Embed(title="Identity Verification Result", color=discord.Color.blue())
                    result_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                    result_embed.add_field(name="Document Status", value=session.last_verification_report.document.status, inline=False)
                    if verification_channel:
                        await verification_channel.send(embed=result_embed)
                    else:
                        await ctx.send(embed=result_embed)
                    break
            else:
                status, session = await check_verification_status(verification_session.id)
                if status == 'cancelled':
                    await self.send_embed(ctx, f"Identity verification for {user.display_name} has been cancelled.", discord.Color.orange())
                elif status in ['consent_declined', 'device_unsupported', 'under_supported_age', 'phone_otp_declined', 'email_verification_declined']:
                    await self.send_embed(ctx, f"Identity verification failed due to {status.replace('_', ' ')}.", discord.Color(0xff4545))
                elif status != 'verified':
                    dm_embed = discord.Embed(
                        title="Verification failed",
                        description=f"Identity verification for {ctx.guild.name} was not completed in time.",
                        color=discord.Color(0xff4545)
                    )
                    await dm_message.edit(embed=dm_embed)
                    stripe.identity.VerificationSession.cancel(verification_session.id)
                else:
                    id_verified_role = ctx.guild.get_role(self.id_verified_role_id)
                    if id_verified_role:
                        await user.add_roles(id_verified_role, reason="Identity verified")
                    verification_channel = self.bot.get_channel(self.verification_channel_id)
                    result_embed = discord.Embed(title="Identity Verification Result", color=discord.Color.blue())
                    result_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                    result_embed.add_field(name="Document Status", value=session.last_verification_report.document.status, inline=False)
                    result_embed.add_field(name="Name", value=session.last_verification_report.document.name, inline=False)
                    result_embed.add_field(name="DOB", value=session.last_verification_report.document.dob, inline=False)
                    result_embed.add_field(name="Address", value=session.last_verification_report.document.address, inline=False)
                    if hasattr(session, 'risk_insights'):
                        result_embed.add_field(name="Risk Insights", value=str(session.risk_insights), inline=False)
                    if verification_channel:
                        await verification_channel.send(embed=result_embed)
                    else:
                        await ctx.send(embed=result_embed)
            await self.config.pending_verification_sessions.set_raw(str(user.id), value=None)
        except stripe.error.StripeError as e:
            embed = discord.Embed(description=f"Failed to create an identity verification session: {e.user_message}", color=discord.Color(0xff4545))
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = discord.Embed(description=f"Failed to send DM to {user.display_name}: {e.text}", color=discord.Color(0xff4545))
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="pendingverifications")
    @checks.admin_or_permissions(manage_guild=True)
    async def pending_verifications(self, ctx):
        """Show all pending verifications for users in the guild."""
        pending_sessions = await self.config.pending_verification_sessions.all()
        guild_member_ids = {member.id for member in ctx.guild.members}
        pending_guild_sessions = {user_id: session_info for user_id, session_info in pending_sessions.items() if int(user_id) in guild_member_ids}

        if not pending_guild_sessions:
            embed = discord.Embed(description="There are no pending verification sessions for users in this guild.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Pending Verification Sessions", color=discord.Color.blue())
        for user_id, session_info in pending_guild_sessions.items():
            member = ctx.guild.get_member(int(user_id))
            if member is None:
                continue  # Skip if the member is not found in the guild
            if session_info is not None:
                # Assuming session_info is a timestamp string, parse it into a datetime object
                try:
                    start_time = datetime.fromisoformat(session_info)
                    time_remaining = discord.utils.format_dt(start_time + timedelta(minutes=15), style='R')
                    embed.add_field(name=f"User: {member.display_name} (ID: {user_id})", value=f"Time remaining: {time_remaining}", inline=False)
                except ValueError:
                    embed.add_field(name=f"User: {member.display_name} (ID: {user_id})", value="Invalid session start time.", inline=False)
            else:
                embed.add_field(name=f"User: {member.display_name} (ID: {user_id})", value="Session info not available.", inline=False)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="verifyme")
    async def verifyme(self, ctx):
        """Allows a user to self-verify their age/ID."""
            
        async def handle_interaction(interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("This button is not for you.", ephemeral=True)
                
            if interaction.custom_id == "yes_button":
                try:
                    session = stripe.identity.VerificationSession.create(
                        type='id_number',
                        metadata={'user_id': str(ctx.author.id)}
                    )
                    embed = discord.Embed(description=f"ID number verification session created. Please complete the verification using this link: {session.url}", color=discord.Color.green())
                    await ctx.send(embed=embed)
                except stripe.error.StripeError as e:
                    embed = discord.Embed(description=f"Failed to create an ID number verification session: {e.user_message}", color=discord.Color(0xff4545))
                    await ctx.send(embed=embed)
            elif interaction.custom_id == "no_button":
                try:
                    session = stripe.identity.VerificationSession.create(
                        type='document',
                        metadata={'user_id': str(ctx.author.id)},
                        document={'allowed_types': ['driving_license']}
                    )
                    embed = discord.Embed(description=f"Document verification session created. Please complete the verification using this link: {session.url}", color=discord.Color.green())
                    await ctx.send(embed=embed)
                except stripe.error.StripeError as e:
                    embed = discord.Embed(description=f"Failed to create a document verification session: {e.user_message}", color=discord.Color(0xff4545))
                    await ctx.send(embed=embed)
            await interaction.response.defer()

        async def handle_verification_completion(interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("This button is not for you.", ephemeral=True)
            
            if interaction.custom_id == "completed_button":
                session_id = interaction.message.embeds[0].description.split("session: ")[1]
                verification_status = await self.check_verification_status(session_id)
                if verification_status == "verified":
                    age_verification_role = discord.utils.get(ctx.guild.roles, name="Age Verified")
                    id_verification_role = discord.utils.get(ctx.guild.roles, name="ID Verified")
                    if age_verification_role:
                        await ctx.author.add_roles(age_verification_role)
                    if id_verification_role:
                        await ctx.author.add_roles(id_verification_role)
                    await interaction.response.send_message("Verification completed and roles assigned.", ephemeral=True)
                else:
                    await interaction.response.send_message("Verification not completed yet. Please try again later.", ephemeral=True)

        embed = discord.Embed(description="Do you have a United States issued ID?", color=discord.Color.blue())
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes_button"))
        view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="no_button"))
        await ctx.send(embed=embed, view=view)

        self.bot.add_view(view)
        self.bot.add_listener(handle_interaction, "on_interaction")

        completion_embed = discord.Embed(description="Click the button below once you have completed the verification session.", color=discord.Color.blue())
        completion_view = discord.ui.View()
        completion_view.add_item(discord.ui.Button(label="Completed", style=discord.ButtonStyle.green, custom_id="completed_button"))
        await ctx.send(embed=completion_embed, view=completion_view)

        self.bot.add_view(completion_view)
        self.bot.add_listener(handle_verification_completion, "on_interaction")
        
    async def check_verification_status(self, session_id):
        """Check the verification status of a session."""
        try:
            session = stripe.identity.VerificationSession.retrieve(session_id)
            return session.status
        except stripe.error.StripeError as e:
            return None

