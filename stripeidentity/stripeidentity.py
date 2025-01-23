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
            id_verified_role=None
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
            dm_embed = discord.Embed(
                title="Age verification requested",
                description=(
                    f"Hello {user.mention},\n\n"
                    f"To enhance safety and security within our community, **{ctx.guild.name}** requires you to verify your age, and link it to your Discord account. \n\n"
                    "> This procedure involves the confirmation of your name and age using a government-issued ID and biometric verification.\n"
                    "### Please ensure you have one of the following documents:\n- **State ID**\n- **Driver's License**\n- **Driver's Permit**\n- **Passport**\n"
                    "### You will also need to:\n- **Provide a valid email address**\n- **Take a series of selfies in a well-lit area**\n- **Submit the identity document mentioned above for biometric matching and analysis**\n\n"
                    "Upon completing the verification, your personal information will be handled according to the following legal agreements:\n- **[BeeHive Terms of Service](<https://www.beehive.systems/tos>)**\n- **[BeeHive Privacy Policy](https://www.beehive.systems/privacy)**\n- **[Stripe Privacy Policy](https://stripe.com/privacy)**\n- **[Stripe Consumer Terms of Service](https://stripe.com/legal/consumer)**\n\n"
                    "Should you choose not to provide your personal information, you can opt out of the verification process by selecting the option below. This action will result in your immediate removal from the server."
                ),
                color=discord.Color(0xff4545)
            )
            dm_embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/id-card.png")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Start verification", url=verification_session.url, style=discord.ButtonStyle.link, emoji="<:globe:1196807971674533968>"))
            
            decline_button = discord.ui.Button(label="Decline verification", style=discord.ButtonStyle.danger)
            async def decline_verification(interaction: discord.Interaction):
                if interaction.user.id == user.id:
                    await interaction.response.send_message(f"You have declined the verification.", ephemeral=True)
            decline_button.callback = decline_verification
            view.add_item(decline_button)
            try:
                dm_message = await user.send(embed=dm_embed, view=view)
            except discord.Forbidden:
                await self.send_embed(ctx, f":x: **Failed to send DM to {user.display_name}**. They might have DMs disabled.", discord.Color(0xff4545))
                return

            await self.send_embed(ctx, f":white_check_mark: **`AGE` verification session created for {user.mention}. They've been sent instructions on how to continue.**", discord.Color(0x2BBD8E))
        except stripe.error.StripeError as e:
            await self.send_embed(ctx, f":x: **Failed to create a verification session**\n`{e.user_message}`", discord.Color(0xff4545))
        except discord.HTTPException as e:
            await self.send_embed(ctx, f":x: **Failed to send DM to {user.display_name}**\n`{e.text}`", discord.Color(0xff4545))
        except AttributeError as e:
            await self.send_embed(ctx, f":x: **An attribute error occurred**\n`{str(e)}`", discord.Color(0xff4545))
        except Exception as e:
            await self.send_embed(ctx, f":x: **An unexpected error occurred**\n`{str(e)}`", discord.Color(0xff4545))

    @commands.command(name="idcheck")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def identity_check(self, ctx: commands.Context, user: discord.Member):
        """
        Perform a biometric verification of a Discord user's real-life identity.
        """
        await ctx.message.delete()
        async with ctx.typing():
            try:
                # Create a verification session
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

                # Prepare the DM embed
                dm_embed = discord.Embed(
                    title="Identity verification required",
                    description=(
                        f"Hello {user.mention},\n\n"
                        f"To enhance safety and security within our community, **{ctx.guild.name}** requires you to verify your identity, and link it to your Discord account. \n\n"
                        "> This procedure involves the confirmation of your identity using a government-issued ID and biometric verification.\n"
                        "### Please ensure you have one of the following documents:\n- **State ID**\n- **Driver's License**\n- **Driver's Permit**\n- **Passport**\n"
                        "### You will also need to:\n- **Provide a valid email address**\n- **Take a series of selfies in a well-lit area**\n- **Submit the identity document mentioned above for biometric matching and analysis**\n\n"
                        "Upon completing the verification, your personal information will be handled according to the following legal agreements:\n- **[BeeHive Terms of Service](<https://www.beehive.systems/tos>)**\n- **[BeeHive Privacy Policy](https://www.beehive.systems/privacy)**\n- **[Stripe Privacy Policy](https://stripe.com/privacy)**\n- **[Stripe Consumer Terms of Service](https://stripe.com/legal/consumer)**\n\n"
                        "Should you choose not to provide your personal information, you can opt out of the verification process by selecting the option below."
                    ),
                    color=discord.Color(0xff4545)
                )
                dm_embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/id-card.png")

                # Create the view with buttons
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Start verification", url=verification_session.url, style=discord.ButtonStyle.link, emoji="<:globe:1196807971674533968>"))
                decline_button = discord.ui.Button(label="Decline verification", style=discord.ButtonStyle.danger)

                # Define the decline verification callback
                async def decline_verification(interaction: discord.Interaction):
                    if interaction.user.id == user.id:
                        await interaction.response.send_message(f"You have declined the verification.", ephemeral=True)
                        await ctx.guild.ban(user, reason="User declined identity verification")

                decline_button.callback = decline_verification
                view.add_item(decline_button)

                # Send the DM to the user
                try:
                    dm_message = await user.send(embed=dm_embed, view=view)
                except discord.Forbidden:
                    await self.send_embed(ctx, f":x: **Failed to send DM to {user.display_name}**. They might have DMs disabled.", discord.Color(0xff4545))
                    return

                # Notify the context that the verification session is open
                await self.send_embed(ctx, f"A verification session is now open. I've sent {user.mention} a message with details on how to continue.", discord.Color(0x2BBD8E))
            except stripe.error.StripeError as e:
                embed = discord.Embed(description=f"Failed to create an identity verification session: {e.user_message}", color=discord.Color(0xff4545))
                await ctx.send(embed=embed)
            except discord.HTTPException as e:
                embed = discord.Embed(description=f"Failed to send DM to {user.display_name}: {e.text}", color=discord.Color(0xff4545))
                await ctx.send(embed=embed)
            except AttributeError as e:
                embed = discord.Embed(description=f"An attribute error occurred: {str(e)}", color=discord.Color(0xff4545))
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"An unexpected error occurred: {str(e)}", color=discord.Color(0xff4545))
                await ctx.send(embed=embed)