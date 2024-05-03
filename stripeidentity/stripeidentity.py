import stripe
from redbot.core import Config, commands, checks
from redbot.core.bot import Red
import discord
import asyncio
from datetime import datetime

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

    @commands.command(name="setverificationchannel")
    @checks.admin_or_permissions(manage_guild=True)
    async def set_verification_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Set the channel where verification results will be sent.
        """
        await self.config.verification_channel.set(channel.id)
        await ctx.send(f"Verification results will now be sent to {channel.mention}.")

    @commands.command(name="setageverifiedrole")
    @checks.admin_or_permissions(manage_roles=True)
    async def set_age_verified_role(self, ctx: commands.Context, role: discord.Role):
        """
        Set the role to give to users who are verified as 18 or older.
        """
        await self.config.age_verified_role.set(role.id)
        await ctx.send(f"Role for age verified users set to {role.name}.")

    @commands.command(name="setidverifiedrole")
    @checks.admin_or_permissions(manage_roles=True)
    async def set_id_verified_role(self, ctx: commands.Context, role: discord.Role):
        """
        Set the role to give to users who have been completely ID verified.
        """
        await self.config.id_verified_role.set(role.id)
        await ctx.send(f"Role for ID verified users set to {role.name}.")

    @commands.command(name="cancelverification")
    @checks.admin_or_permissions(manage_guild=True)
    async def cancel_verification(self, ctx: commands.Context, user: discord.Member):
        """
        Cancel a pending verification session for a user.
        """
        session_id = await self.config.pending_verification_sessions.get_raw(user.id)
        if session_id:
            try:
                stripe.post(f"/v1/identity/verification_sessions/{session_id}/cancel")
                await ctx.send(f"Verification session for {user.display_name} has been canceled.")
            except stripe.error.StripeError as e:
                await ctx.send(f"Failed to cancel the verification session: {e.user_message}")
            finally:
                await self.config.pending_verification_sessions.set_raw(user.id, value=None)
        else:
            await ctx.send(f"No pending verification session found for {user.display_name}.")

    @commands.command(name="agecheck")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def age_check(self, ctx: commands.Context, user: discord.Member):
        """
        Perform an age check on a user using Stripe Identity.
        """
        try:
            verification_session = stripe.identity.VerificationSession.create(
                type='document',
                options={
                    'document': {
                        'allowed_types': ['driving_license', 'passport', 'id_card'],
                        'require_id_number': True,
                        'require_live_capture': True,
                        'require_matching_selfie': True,
                    },
                }
            )
            await self.config.pending_verification_sessions.set_raw(user.id, value=verification_session.id)
            dm_message = await user.send(
                f"Hello {user.mention},\n"
                "To remain in the server, you need to prove you are **18+** "
                "Please complete the verification using the following link: "
                f"[Click here to verify your age securely]({verification_session.url})\n"
                "You have 15 minutes to complete this process. If you do not complete verification, you will be removed from the server for safety."
            )
            await ctx.send(f"Verification session created for {user.display_name}. Instructions have been sent via DM.")

            async def check_verification_status(session_id):
                session = stripe.identity.VerificationSession.retrieve(session_id)
                return session.status == 'verified', session

            await asyncio.sleep(900)  # Wait for 15 minutes
            verified, session = await check_verification_status(verification_session.id)
            if not verified:
                await ctx.guild.kick(user, reason="Did not verify age")
                await dm_message.edit(content=f"Verification was not completed in time. You have been removed from the server {ctx.guild.name}.")
            else:
                verification_channel = self.bot.get_channel(self.verification_channel_id)
                if verification_channel:
                    dob = datetime.fromisoformat(session.last_verification_report.document.dob)
                    age = (datetime.now() - dob).days // 365
                    if age < 18:
                        await ctx.guild.ban(user, reason="User is underage - ID Validated by BeeHive")
                        await dm_message.edit(content="You have been banned from the server because you are under 18.\nYou may return once you are 18 years of age or older...\n\nPlease don't take this ban personally - we're sure you're a great person to meet and interact with, but...the internet can be a dangerous place sometimes, and this is as much to keep us safe as it is to keep you safe.")
                    else:
                        age_verified_role = ctx.guild.get_role(self.age_verified_role_id)
                        if age_verified_role:
                            await user.add_roles(age_verified_role, reason="Age verified as 18+")
                        embed = discord.Embed(title="Age Verification Result", color=discord.Color.green())
                        embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                        embed.add_field(name="Age", value=str(age), inline=False)
                        await verification_channel.send(embed=embed)
            await self.config.pending_verification_sessions.set_raw(user.id, value=None)
        except stripe.error.StripeError as e:
            await ctx.send(f"Failed to create a verification session: {e.user_message}")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to send DM to {user.display_name}: {e.text}")

    @commands.command(name="identitycheck")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def identity_check(self, ctx: commands.Context, user: discord.Member):
        """
        Perform a full identity check on a user using Stripe Identity.
        """
        try:
            verification_session = stripe.post(
                "/v1/identity/verification_sessions",
                params={
                    'type': 'identity',
                    'options': {
                        'document': {
                            'allowed_types': ['driving_license', 'passport', 'id_card'],
                            'require_id_number': True,
                            'require_live_capture': True,
                            'require_matching_selfie': True,
                        },
                    },
                }
            )
            await self.config.pending_verification_sessions.set_raw(user.id, value=verification_session.id)
            dm_message = await user.send(
                f"Hello {user.mention},\n"
                "To access certain features of the server, we require a full identity verification process. "
                "Please complete the verification using the following link: "
                f"{verification_session.url}\n"
                "You have 15 minutes to complete this process."
            )
            await ctx.send(f"Identity verification session created for {user.display_name}. Instructions have been sent via DM.")

            async def check_verification_status(session_id):
                session = stripe.get(f"/v1/identity/verification_sessions/{session_id}")
                return session.status == 'verified', session

            await asyncio.sleep(900)  # Wait for 15 minutes
            verified, session = await check_verification_status(verification_session.id)
            if not verified:
                await ctx.guild.kick(user, reason="Did not verify identity")
                await dm_message.edit(content=f"Identity verification was not completed in time. You have been removed from the server {ctx.guild.name}.")
            else:
                id_verified_role = ctx.guild.get_role(self.id_verified_role_id)
                if id_verified_role:
                    await user.add_roles(id_verified_role, reason="Identity verified")
                verification_channel = self.bot.get_channel(self.verification_channel_id)
                if verification_channel:
                    embed = discord.Embed(title="Identity Verification Result", color=discord.Color.blue())
                    embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                    embed.add_field(name="Document Status", value=session.last_verification_report.document.status, inline=False)
                    embed.add_field(name="Name", value=session.last_verification_report.document.name, inline=False)
                    embed.add_field(name="DOB", value=session.last_verification_report.document.dob, inline=False)
                    embed.add_field(name="Address", value=session.last_verification_report.document.address, inline=False)
                    if hasattr(session, 'risk_insights'):
                        embed.add_field(name="Risk Insights", value=str(session.risk_insights), inline=False)
                    await verification_channel.send(embed=embed)
            await self.config.pending_verification_sessions.set_raw(user.id, value=None)
        except stripe.error.StripeError as e:
            await ctx.send(f"Failed to create an identity verification session: {e.user_message}")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to send DM to {user.display_name}: {e.text}")
