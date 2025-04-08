import discord
from redbot.core import commands, Config, app_commands
from datetime import datetime, timedelta, timezone
import aiohttp
import stripe

class ChatSummary(commands.Cog):
    """Cog to summarize chat activity for users."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_user = {"customer_id": None, "is_afk": False}
        self.config.register_user(**default_user)

    @commands.group(name="summarizer")
    async def summarizer(self, ctx: commands.Context):
        """Group for summarizer related commands."""
        pass

    @commands.group(name="summarize")
    async def summarize(self, ctx: commands.Context):
        """Group for summarize related commands."""
        pass

    @summarize.command(name="recent")
    async def chat_summary(self, ctx: commands.Context):
        """Summarize recent channel activity"""
        try:
            guild = ctx.guild
            if not guild:
                await ctx.send("This command can only be used in a server.", delete_after=10)
                return

            user_data = await self.config.user(ctx.author).all()
            customer_id = user_data.get("customer_id")
            hours = 8 if customer_id else 2

            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            recent_messages = []
            mentions = []

            channel = ctx.channel
            if not channel:
                await ctx.send("This command can only be used in a text channel.", delete_after=10)
                return

            async with ctx.typing():
                async for message in channel.history(limit=1000, after=cutoff):
                    if not message.author.bot:
                        recent_messages.append({
                            "author": message.author.display_name,
                            "content": message.content,
                            "timestamp": message.created_at.isoformat()
                        })
                        if ctx.author in message.mentions:
                            mentions.append({
                                "author": message.author.display_name,
                                "timestamp": message.created_at,
                                "jump_url": message.jump_url
                            })

                messages_content = "\n".join(f"{msg['author']}: {msg['content']}" for msg in recent_messages)
                openai_url = "https://api.openai.com/v1/chat/completions"
                tokens = await self.bot.get_shared_api_tokens("openai")
                openai_key = tokens.get("api_key") if tokens else None

                ai_summary = await self._generate_ai_summary(openai_key, messages_content, customer_id)
                mention_summary = self._generate_mention_summary(mentions)
                await self._send_summary_embed(ctx, ai_summary, mention_summary, customer_id)

                if openai_key and customer_id:
                    await self._track_stripe_event(customer_id)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}", delete_after=10)

    async def _generate_ai_summary(self, openai_key, messages_content, customer_id):
        openai_url = "https://api.openai.com/v1/chat/completions"
        if openai_key:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            messages = [
                {"role": "system", "content": "You are a chat summary generator. Use title-less bulletpoints where appropriate."},
                {"role": "user", "content": f"Summarize the following chat messages: {messages_content}"}
            ]
            model = "o3-mini" if customer_id else "gpt-4o-mini"
            openai_payload = {
                "model": model,
                "messages": messages,
                "temperature": 1.0
            }
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(openai_url, headers=headers, json=openai_payload) as openai_response:
                        if openai_response.status == 200:
                            openai_data = await openai_response.json()
                            return openai_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        else:
                            return f"Failed to generate summary from OpenAI. Status code: {openai_response.status}"
                except aiohttp.ClientError as e:
                    return f"Failed to connect to OpenAI API: {str(e)}"
        else:
            return "OpenAI API key not configured."

    def _generate_mention_summary(self, mentions):
        if not mentions:
            return "No mentions in the recent messages."
        # Sort mentions by timestamp in descending order and take the last 5
        recent_mentions = sorted(mentions, key=lambda x: x['timestamp'], reverse=True)[:5]
        return "\n".join(f"**{mention['author']}** *<t:{int(mention['timestamp'].timestamp())}:R>* **[Jump]({mention['jump_url']})**" for mention in recent_mentions)

    async def _send_summary_embed(self, ctx, ai_summary, mention_summary, customer_id):
        embed = discord.Embed(
            title="AI chat summary",
            description=ai_summary or "No recent messages.",
            color=0xfffffe
        )
        embed.add_field(name="Who mentioned you", value=mention_summary, inline=False)
        if not customer_id:
            embed.set_footer(text="You're using the free version of BeeHive's AI summarizer. Upgrade for improved speed, intelligence, and functionality.")
        else:
            embed.set_footer(text="You're powered up with premium AI models and extended discussion context.")
        await ctx.send(embed=embed)

    async def _track_stripe_event(self, customer_id):
        stripe_tokens = await self.bot.get_shared_api_tokens("stripe")
        stripe_key = stripe_tokens.get("api_key") if stripe_tokens else None

        if stripe_key:
            stripe_url = "https://api.stripe.com/v1/billing/meter_events"
            stripe_headers = {
                "Authorization": f"Bearer {stripe_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            stripe_payload = {
                "event_name": "summary_generated",
                "timestamp": int(datetime.now().timestamp()),
                "payload[stripe_customer_id]": customer_id
            }
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(stripe_url, headers=stripe_headers, data=stripe_payload) as stripe_response:
                        if stripe_response.status != 200:
                            await ctx.send(f"Failed to track event with Stripe. Status code: {stripe_response.status}", delete_after=10)
                except aiohttp.ClientError as e:
                    await ctx.send(f"Failed to connect to Stripe API: {str(e)}", delete_after=10)

    @summarizer.command(name="id")
    @commands.is_owner()
    async def set_customer_id(self, ctx: commands.Context, user: discord.User):
        """Set a customer's ID for a user globally using a button and modal."""
        
        class CustomerIDModal(discord.ui.Modal, title="Enter Customer ID"):
            customer_id = discord.ui.TextInput(label="Customer ID", placeholder="Enter the customer ID here")

            async def on_submit(self, interaction: discord.Interaction):
                await self.config.user(user).customer_id.set(self.customer_id.value)
                await interaction.response.send_message(f"Customer ID for {user.name} has been set.", ephemeral=True)

        class CustomerIDButton(discord.ui.View):
            @discord.ui.button(label="Set Customer ID", style=discord.ButtonStyle.primary)
            async def set_id_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    return
                await interaction.response.send_modal(CustomerIDModal())

        await ctx.send("Click the button below to set the customer ID.", view=CustomerIDButton())

    @summarizer.command(name="profile")
    async def view_profile(self, ctx: commands.Context):
        """View your own summarizer profile."""
        user = ctx.author
        user_data = await self.config.user(user).all()
        customer_id = user_data.get("customer_id", "Not set")

        embed = discord.Embed(
            title=f"{user.name}'s summarizer profile",
            color=0xfffffe
        )

        if isinstance(ctx.channel, discord.DMChannel):
            embed.add_field(name="Customer ID", value=customer_id, inline=False)
        else:
            embed.add_field(name="Customer ID", value="Hidden (viewable in DMs only)", inline=False)

        if customer_id != "Not set":
            stripe_tokens = await self.bot.get_shared_api_tokens("stripe")
            stripe_key = stripe_tokens.get("api_key") if stripe_tokens else None

            if stripe_key:
                async def generate_billing_link(interaction):
                    if interaction.user != ctx.author:
                        await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                        return

                    async with aiohttp.ClientSession() as session:
                        try:
                            stripe_url = "https://api.stripe.com/v1/billing_portal/sessions"
                            stripe_headers = {
                                "Authorization": f"Bearer {stripe_key}",
                                "Content-Type": "application/x-www-form-urlencoded"
                            }
                            stripe_payload = {
                                "customer": customer_id,
                                "return_url": ctx.channel.jump_url
                            }
                            async with session.post(stripe_url, headers=stripe_headers, data=stripe_payload) as stripe_response:
                                if stripe_response.status == 200:
                                    response_data = await stripe_response.json()
                                    login_url = response_data.get("url")
                                    if login_url:
                                        await interaction.response.send_message(f"Click **[here](<{login_url}>)** to manage your billing.\n\n:octagonal_sign: This link will automatically sign you in - **don't share it with others no matter what**.", ephemeral=True)
                                else:
                                    await interaction.response.send_message(f"Failed to generate billing portal link. Status code: {stripe_response.status}", ephemeral=True)
                        except aiohttp.ClientError as e:
                            await interaction.response.send_message(f"Failed to connect to Stripe API: {str(e)}", ephemeral=True)

                view = discord.ui.View(timeout=30)
                button = discord.ui.Button(label="Login and manage billing", style=discord.ButtonStyle.green)
                button.callback = generate_billing_link
                view.add_item(button)
                await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed)

    @summarizer.command(name="upgrade")
    async def upgrade_info(self, ctx: commands.Context):
        """Explain the perks of upgrading by adding a customer ID."""
        embed = discord.Embed(
            title="Go premium, get more",
            color=0xfffffe
        )
        embed.add_field(
            name="Access to frontier AI models",
            value="Gain access to advanced AI models that provide more accurate and faster summaries.",
            inline=False
        )
        embed.add_field(
            name="Extended discussion context",
            value="Benefit from extended discussion context, allowing for more comprehensive summaries. (Summarizes up to 8 hours of chat history instead of 2)",
            inline=False
        )
        embed.add_field(
            name="Priority new feature access",
            value="Enjoy priority access to new features and updates as they become available.",
            inline=False
        )
        embed.add_field(
            name="Longer chat history support",
            value="Receive support for summarizing longer chat histories, enhancing your experience.",
            inline=False
        )
        embed.set_footer(text="Upgrade today to enhance your summarization experience!")
        await ctx.send(embed=embed)

    @commands.command(name="away")
    async def set_away(self, ctx: commands.Context, *, reason: str = "AFK"):
        """Set your status to away with an optional reason."""
        await self.config.user(ctx.author).is_afk.set(True)
        await ctx.send(f"{ctx.author.display_name} is now set to AFK: {reason}")

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot:
            return

        user_data = await self.config.user(message.author).all()
        if user_data.get("is_afk"):
            await self.config.user(message.author).is_afk.set(False)
            await message.channel.send(f"Welcome back, {message.author.display_name}! You are no longer marked as AFK.")
            ctx = await self.bot.get_context(message)
            await self.chat_summary(ctx)

        for user in message.mentions:
            if user.bot:
                continue
            user_data = await self.config.user(user).all()
            if user_data.get("is_afk"):
                await message.channel.send(f"{user.display_name} is currently AFK and may not respond immediately.")
