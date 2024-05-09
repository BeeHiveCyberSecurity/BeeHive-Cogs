from redbot.core import Config, commands
import discord
from discord.ui import Button, View
from datetime import datetime, timedelta  # Added timedelta import

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

    @commands.hybrid_command(name="orchestrator")
    @commands.is_owner()
    async def orchestrator(self, ctx):
        """See and manage the servers that your bot instance is in."""
        await ctx.defer()
        guilds = []
        async for guild in self.bot.fetch_guilds(limit=None):
            guilds.append(guild)
        if not guilds:
            return await ctx.send("No guilds available.")

        # Ensure that member_count is not None before sorting
        guilds_sorted = sorted((guild for guild in guilds if guild.member_count is not None), key=lambda x: x.member_count, reverse=True)

        embeds = []
        guild_ids = []
        for guild in guilds_sorted:
            try:
                full_guild = await self.bot.fetch_guild(guild.id)
                if not full_guild:
                    continue
                guild_owner = await self.bot.fetch_user(full_guild.owner_id) if full_guild.owner_id else 'Unknown'
                # Calculate activity score based on message count in the past week
                one_week_ago = datetime.utcnow() - timedelta(days=7)
                messages_past_week = 0  # Initialize message count
                for channel in full_guild.text_channels:
                    try:
                        messages_past_week += sum(1 async for _ in channel.history(after=one_week_ago))
                    except discord.Forbidden:
                        # Bot does not have permissions to read message history in this channel
                        pass
                # Check if there are members in the guild to avoid division by zero
                member_count = full_guild.member_count if full_guild.member_count else 1
                activity_score = messages_past_week / member_count  # Messages per member

                # Determine activity level based on the score
                if activity_score > 1:
                    activity_level = "High"
                elif activity_score > 0.1:
                    activity_level = "Medium"
                else:
                    activity_level = "Low"

                embed_color = discord.Color.from_rgb(255, 255, 254)
                # Fetch the full member list to get an accurate count
                full_member_list = await full_guild.query_members(limit=None)
                accurate_member_count = len(full_member_list)
                embed_description = (
                    f"**Members:** `{accurate_member_count}`\n"
                    f"**Owner:** `{guild_owner}`\n"
                    f"**Created At:** `{full_guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                    f"**Boost Level:** `{full_guild.premium_tier}`\n"
                    f"**Boosts:** `{full_guild.premium_subscription_count}`\n"
                    f"**Features:** `{', '.join(full_guild.features) if full_guild.features else 'None'}`\n"
                    f"**Activity Level (Past Week):** `{activity_level}`"
                )
                embed = discord.Embed(title=full_guild.name, description=embed_description, color=embed_color)
                embed.set_thumbnail(url=full_guild.icon.url if full_guild.icon else None)
                embed.add_field(name="Guild ID", value=str(full_guild.id))
                embed.add_field(name="Verification Level", value=str(full_guild.verification_level) if full_guild.verification_level else "None")
                embed.add_field(name="Explicit Content Filter", value=str(full_guild.explicit_content_filter))
                embed.add_field(name="Number of Roles", value=str(len(full_guild.roles)))
                embed.add_field(name="Number of Emojis", value=str(len(full_guild.emojis)))
                embed.add_field(name="Number of Text Channels", value=str(len(full_guild.text_channels)))
                embed.add_field(name="Number of Voice Channels", value=str(len(full_guild.voice_channels)))
                embeds.append(embed)
                guild_ids.append(full_guild.id)
            except Exception as e:
                print(f"Failed to fetch guild {guild.id} due to {str(e)}")
                continue

        # Paginator view with buttons
        class PaginatorView(View):
            def __init__(self, embeds, guild_ids):
                super().__init__()
                self.embeds = embeds
                self.guild_ids = guild_ids
                self.current_page = 0
                self.invite_button = Button(emoji="🔗", label="Generate invite", style=discord.ButtonStyle.secondary, row=1, custom_id="invite_btn")
                self.leave_button = Button(emoji="🗑️", label="Leave server", style=discord.ButtonStyle.danger, row=1, custom_id="leave_btn")
                self.previous_button = Button(label="Previous", style=discord.ButtonStyle.primary, row=2, custom_id="previous_btn")
                self.next_button = Button(label="Next", style=discord.ButtonStyle.primary, row=2, custom_id="next_btn")
                self.add_item(self.previous_button)
                self.add_item(self.next_button)
                self.add_item(self.invite_button)
                self.add_item(self.leave_button)
            
            async def interaction_check(self, interaction):
                return interaction.user == ctx.author
            
            async def on_timeout(self):
                self.previous_button.disabled = True
                self.next_button.disabled = True
                self.invite_button.disabled = True
                self.leave_button.disabled = True
                self.stop()

            async def previous_button_callback(self, interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
            
            async def next_button_callback(self, interaction):
                if self.current_page < len(self.embeds) - 1:
                    self.current_page += 1
                    await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
            
            async def invite_button_callback(self, interaction):
                guild_id = self.guild_ids[self.current_page]
                guild = self.bot.get_guild(guild_id)
                if guild:
                    invites = await guild.invites()
                    if invites:
                        invite = invites[0]  # Use the first available invite
                    else:
                        # If no invites are available, try to create one if the bot has permissions
                        if guild.me.guild_permissions.create_instant_invite:
                            invite = await guild.text_channels[0].create_invite(max_age=300)  # Invite expires after 5 minutes
                        else:
                            invite = None
                    if invite:
                        await interaction.response.send_message(f"Invite for {guild.name}: {invite.url}", ephemeral=True)
                    else:
                        await interaction.response.send_message("No available invites and cannot create one.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Could not access guild with ID: {guild_id}", ephemeral=True)
            
            async def leave_button_callback(self, interaction):
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
                    await interaction.message.edit(embed=self.embeds[self.current_page] if self.embeds else None, view=self)
                else:
                    await interaction.response.send_message(f"Could not leave guild with ID: {guild_id}", ephemeral=True)
        
        paginator_view = PaginatorView(embeds, guild_ids)
        paginator_view.invite_button.callback = paginator_view.invite_button_callback
        paginator_view.leave_button.callback = paginator_view.leave_button_callback
        paginator_view.previous_button.callback = paginator_view.previous_button_callback
        paginator_view.next_button.callback = paginator_view.next_button_callback
        
        if embeds:
            await ctx.send(embed=embeds[0], view=paginator_view)
        else:
            await ctx.send("No embeds available.", view=paginator_view)
