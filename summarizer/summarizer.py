import discord
from redbot.core import commands, Config, app_commands
from datetime import datetime, timedelta

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
    async def chat_summary(self, ctx: commands.Context):
        """Get a summary of the chat activity from the last 2 or 4 hours."""
        guild = ctx.guild
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return

        user_data = await self.config.user(ctx.author).all()
        customer_id = user_data.get("customer_id")
        hours = 4 if customer_id else 2

        cutoff = datetime.now() - timedelta(hours=hours)
        recent_messages = []

        async for message in guild.text_channels[0].history(limit=1000, after=cutoff):
            if not message.author.bot:
                recent_messages.append({
                    "author": message.author.name,
                    "content": message.content,
                    "timestamp": message.created_at.isoformat()
                })

        summary = "\n".join(f"{msg['author']}: {msg['content']}" for msg in recent_messages[-10:])
        embed = discord.Embed(
            title="AI chat summary",
            description=summary or "No recent messages.",
            color=0xfffffe
        )
        await ctx.send(embed=embed)

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
