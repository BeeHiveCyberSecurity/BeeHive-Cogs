import discord
from redbot.core import commands, Config, app_commands
from datetime import datetime, timedelta
import aiohttp

class ChatSummary(commands.Cog):
    """Cog to summarize chat activity for users."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_user = {
            "customer_id": None
        }
        self.config.register_user(**default_user)

    @app_commands.command(name="chatsummary")
    async def chat_summary(self, interaction: discord.Interaction):
        """Get a summary of the chat activity from the last 2 or 4 hours."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        user_data = await self.config.user(interaction.user).all()
        customer_id = user_data.get("customer_id")
        hours = 4 if customer_id else 2

        cutoff = datetime.now() - timedelta(hours=hours)
        recent_messages = []

        # Gather messages from the channel where the command is run
        channel = interaction.channel
        if not channel:
            await interaction.response.send_message("This command can only be used in a text channel.", ephemeral=True)
            return

        async for message in channel.history(limit=1000, after=cutoff):
            if not message.author.bot:
                recent_messages.append({
                    "author": message.author.name,
                    "content": message.content,
                    "timestamp": message.created_at.isoformat()
                })

        # Prepare the data for OpenAI request
        messages_content = "\n".join(f"{msg['author']}: {msg['content']}" for msg in recent_messages)
        openai_url = "https://api.openai.com/v1/chat/completions"
        tokens = await self.bot.get_shared_api_tokens("openai")
        openai_key = tokens.get("api_key") if tokens else None

        if openai_key:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            messages = [
                {"role": "system", "content": "You are a chat summary generator."},
                {"role": "user", "content": f"Summarize the following chat messages: {messages_content}"}
            ]
            openai_payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 1.0
            }
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(openai_url, headers=headers, json=openai_payload) as openai_response:
                        if openai_response.status == 200:
                            openai_data = await openai_response.json()
                            ai_summary = openai_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        else:
                            ai_summary = f"Failed to generate summary from OpenAI. Status code: {openai_response.status}"
                except aiohttp.ClientError as e:
                    ai_summary = f"Failed to connect to OpenAI API: {str(e)}"
        else:
            ai_summary = "OpenAI API key not configured."

        embed = discord.Embed(
            title="AI chat summary",
            description=ai_summary or "No recent messages.",
            color=0xfffffe
        )
        await interaction.response.send_message(embed=embed)

    @commands.group(name="summarizer", invoke_without_command=True)
    async def summarizer(self, ctx: commands.Context):
        """Group for summarizer related commands."""
        await ctx.send("Use a subcommand for specific actions.")

    @summarizer.command(name="setcustomerid")
    @commands.is_owner()
    async def set_customer_id(self, ctx: commands.Context, user: discord.User, customer_id: str):
        """Set a customer's ID for a user globally."""
        await self.config.user(user).customer_id.set(customer_id)
        await ctx.send(f"Customer ID for {user.name} has been set to {customer_id}.")

    @summarizer.command(name="profile")
    async def view_profile(self, ctx: commands.Context, user: discord.User = None):
        """View a user's summarizer profile."""
        user = user or ctx.author
        user_data = await self.config.user(user).all()
        customer_id = user_data.get("customer_id", "Not set")

        embed = discord.Embed(
            title=f"{user.name}'s summarizer profile",
            color=0xfffffe
        )
        embed.add_field(name="Customer ID", value=customer_id, inline=False)
        await ctx.send(embed=embed)
