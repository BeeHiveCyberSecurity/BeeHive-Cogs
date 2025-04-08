import discord
from discord.ext import tasks
from redbot.core import commands, Config
from datetime import datetime, timedelta

class ChatSummary(commands.Cog):
    """Cog to summarize chat activity for users."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_guild = {
            "messages": []
        }
        default_user = {
            "customer_id": None
        }
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.cleanup_old_messages.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild = message.guild
        if guild:
            async with self.config.guild(guild).messages() as messages:
                messages.append({
                    "author": message.author.name,
                    "content": message.content,
                    "timestamp": message.created_at.isoformat()
                })

    @tasks.loop(hours=1)
    async def cleanup_old_messages(self):
        for guild in self.bot.guilds:
            async with self.config.guild(guild).messages() as messages:
                cutoff = datetime.now() - timedelta(hours=4)
                messages[:] = [msg for msg in messages if datetime.fromisoformat(msg["timestamp"]) > cutoff]

    @commands.slash_command(name="chatsummary")
    async def chat_summary(self, ctx: commands.Context):
        """Get a summary of the chat activity from the last 2 or 4 hours."""
        guild = ctx.guild
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return

        user_data = await self.config.user(ctx.author).all()
        customer_id = user_data.get("customer_id")
        hours = 4 if customer_id else 2

        messages = await self.config.guild(guild).messages()
        if not messages:
            await ctx.send(f"No messages to summarize from the last {hours} hours.")
            return

        cutoff = datetime.now() - timedelta(hours=hours)
        recent_messages = [msg for msg in messages if datetime.fromisoformat(msg["timestamp"]) > cutoff]
        summary = "\n".join(f"{msg['author']}: {msg['content']}" for msg in recent_messages[-10:])
        embed = discord.Embed(
            title="AI chat summary",
            description=summary or "No recent messages.",
            color=0xfffffe
        )
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_guild=True)
    @commands.slash_command(name="setcustomerid")
    async def set_customer_id(self, ctx: commands.Context, user: discord.User, customer_id: str):
        """Set a customer's ID for a user globally."""
        await self.config.user(user).customer_id.set(customer_id)
        await ctx.send(f"Customer ID for {user.name} has been set to {customer_id}.")

    def cog_unload(self):
        self.cleanup_old_messages.cancel()
