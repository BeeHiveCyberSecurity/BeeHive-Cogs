from redbot.core import Config, commands
import discord
from discord.ui import View

class Orchestrator(commands.Cog):
    """See info about the servers your bot is in.
    
    For bot owners only.
    """

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=806715409318936616)
        self.bot = bot

    # This cog does not store any End User Data
    async def red_get_data_for_user(self, *, user_id: int):
        return {}
    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        pass

    @commands.hybrid_command(name="orchestrator", aliases=["botservers"])
    @commands.is_owner()
    async def orchestrator(self, ctx):
        """See and manage the servers that your bot instance is in."""
        await ctx.defer()
        guilds = [guild async for guild in self.bot.fetch_guilds(limit=None)]
        guilds_sorted = sorted(guilds, key=lambda x: x.member_count if hasattr(x, 'member_count') and x.member_count is not None else 0, reverse=True)
        if not guilds_sorted:
            return await ctx.send("No guilds available.")

        embeds = []
        guild_ids = []
        for guild in guilds_sorted:
            full_guild = await self.bot.fetch_guild(guild.id)
            embed_color = discord.Color.from_rgb(255, 255, 254)
            guild_owner = full_guild.owner_id if hasattr(full_guild, 'owner_id') else 'Unknown'
            member_count = full_guild.member_count if hasattr(full_guild, 'member_count') else 'Unknown'
            embed_description = (
                f"**Members:** `{member_count}`\n"
                f"**Owner:** <@{guild_owner}>\n"
                f"**Created At:** `{full_guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                f"**Boost Level:** `{full_guild.premium_tier}`\n"
                f"**Boosts:** `{full_guild.premium_subscription_count}`\n"
                f"**Features:** `{', '.join(full_guild.features) if full_guild.features else 'None'}`"
            )
            embed = discord.Embed(title=guild.name, description=embed_description, color=embed_color)
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(name="Guild ID", value=str(guild.id))
            embed.add_field(name="Verification Level", value=str(guild.verification_level) if guild.verification_level else "None")
            embed.add_field(name="Explicit Content Filter", value=str(guild.explicit_content_filter.name) if guild.explicit_content_filter else "None")
            embed.add_field(name="Number of Roles", value=str(len(full_guild.roles)) if hasattr(full_guild, 'roles') else 'Unknown')
            embed.add_field(name="Number of Emojis", value=str(len(full_guild.emojis)) if hasattr(full_guild, 'emojis') else 'Unknown')
            text_channels = [channel for channel in full_guild.channels if isinstance(channel, discord.TextChannel)]
            voice_channels = [channel for channel in full_guild.channels if isinstance(channel, discord.VoiceChannel)]
            embed.add_field(name="Number of Text Channels", value=str(len(text_channels)) if len(text_channels) > 0 else '0')
            embed.add_field(name="Number of Voice Channels", value=str(len(voice_channels)) if len(voice_channels) > 0 else '0')
            embeds.append(embed)
            guild_ids.append(guild.id)
        
        # Paginator view with buttons
        class PaginatorView(View):
            def __init__(self, embeds, guild_ids):
                super().__init__(timeout=60)
                self.embeds = embeds
                self.guild_ids = guild_ids
                self.current_page = 0
                self.message = None
            
            async def interaction_check(self, interaction):
                return interaction.user == ctx.author
            
            async def on_timeout(self):
                if self.message:
                    await self.message.edit(view=None)
                self.stop()

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
            async def previous_page(self, button, interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    await interaction.response.edit_message(embed=self.embeds[self.current_page])

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
            async def next_page(self, button, interaction):
                if self.current_page < len(self.embeds) - 1:
                    self.current_page += 1
                    await interaction.response.edit_message(embed=self.embeds[self.current_page])

            @discord.ui.button(label="🔗", style=discord.ButtonStyle.secondary)
            async def create_invite(self, button, interaction):
                guild_id = self.guild_ids[self.current_page]
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    await interaction.response.send_message(f"Unable to access guild with ID: {guild_id}", ephemeral=True)
                    return

                # Check if the bot has permissions to create an invite
                if guild.me.guild_permissions.create_instant_invite:
                    try:
                        # Try to get an existing invite
                        invites = await guild.invites()
                        invite = invites[0] if invites else None
                        # If no existing invites, create a new one
                        if not invite:
                            # Check if the guild has text channels before creating an invite
                            if guild.text_channels:
                                invite = await guild.text_channels[0].create_invite(max_age=300)  # Invite expires after 5 minutes
                            else:
                                await interaction.response.send_message("Guild does not have any text channels to create an invite.", ephemeral=True)
                                return
                    except Exception as e:
                        await interaction.response.send_message(f"Unable to create an invite: {str(e)}", ephemeral=True)
                        return
                else:
                    await interaction.response.send_message("Bot does not have permissions to create an invite.", ephemeral=True)
                    return

                await interaction.response.send_message(f"Invite for {guild.name}: {invite.url}", ephemeral=True)

            @discord.ui.button(label="🗑️", style=discord.ButtonStyle.danger)
            async def leave_guild(self, button, interaction):
                guild_id = self.guild_ids[self.current_page]
                guild = self.bot.get_guild(guild_id)
                if guild:
                    await guild.leave()
                    await interaction.response.send_message(f"Left guild: {guild.name} (ID: {guild_id})", ephemeral=True)
                    # Update the embeds and guild_ids to reflect the change
                    del self.embeds[self.current_page]
                    del self.guild_ids[self.current_page]
                    # If the current page is now out of range, move back one
                    if self.current_page >= len(self.embeds):
                        self.current_page = max(len(self.embeds) - 1, 0)
                    # Update the message with the new current page embed
                    await self.message.edit(embed=self.embeds[self.current_page] if self.embeds else None)
                else:
                    await interaction.response.send_message(f"Could not leave guild with ID: {guild_id}", ephemeral=True)
        
        paginator_view = PaginatorView(embeds, guild_ids)
        
        paginator_view.message = await ctx.send(embed=embeds[0], view=paginator_view)
