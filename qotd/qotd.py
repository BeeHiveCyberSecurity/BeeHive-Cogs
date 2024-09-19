import discord
from redbot.core import commands, Config
import random
import os
import json

class QotD(commands.Cog):
    """Question of the Day Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled_categories": [],
            "current_question": None
        }
        self.config.register_guild(**default_guild)
        self.data_path = os.path.join(os.path.dirname(__file__), "data")
        self.categories = self.load_categories()

    def load_categories(self):
        categories = {}
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        for filename in os.listdir(self.data_path):
            if filename.endswith(".json"):
                with open(os.path.join(self.data_path, filename), "r") as f:
                    category_name = filename[:-5]
                    categories[category_name] = json.load(f)
        return categories

    @commands.guild_only()
    @commands.group()
    async def qotd(self, ctx):
        """Question of the Day commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @qotd.command()
    async def list_categories(self, ctx):
        """List all available question categories"""
        if self.categories:
            category_list = "\n".join(self.categories.keys())
            await ctx.send(f"Available categories:\n{category_list}")
        else:
            await ctx.send("No categories available.")

    @qotd.command()
    async def enable_category(self, ctx, category: str):
        """Enable a question category"""
        if category in self.categories:
            async with self.config.guild(ctx.guild).enabled_categories() as enabled_categories:
                if category not in enabled_categories:
                    enabled_categories.append(category)
                    await ctx.send(f"Category enabled: {category}")
                else:
                    await ctx.send(f"Category already enabled: {category}")
        else:
            await ctx.send("Invalid category.")

    @qotd.command()
    async def disable_category(self, ctx, category: str):
        """Disable a question category"""
        async with self.config.guild(ctx.guild).enabled_categories() as enabled_categories:
            if category in enabled_categories:
                enabled_categories.remove(category)
                await ctx.send(f"Category disabled: {category}")
            else:
                await ctx.send("Category not enabled.")

    @qotd.command()
    async def list_enabled(self, ctx):
        """List all enabled question categories"""
        enabled_categories = await self.config.guild(ctx.guild).enabled_categories()
        if enabled_categories:
            category_list = "\n".join(enabled_categories)
            await ctx.send(f"Enabled categories:\n{category_list}")
        else:
            await ctx.send("No categories enabled.")

    @qotd.command()
    async def ask(self, ctx):
        """Ask a random question of the day from enabled categories"""
        enabled_categories = await self.config.guild(ctx.guild).enabled_categories()
        if enabled_categories:
            questions = []
            for category in enabled_categories:
                questions.extend(self.categories.get(category, []))
            if questions:
                question = random.choice(questions)
                await self.config.guild(ctx.guild).current_question.set(question)
                await ctx.send(f"Question of the Day: {question}")
            else:
                await ctx.send("No questions available in the enabled categories.")
        else:
            await ctx.send("No categories enabled.")

    @qotd.command()
    async def current(self, ctx):
        """Show the current question of the day"""
        current_question = await self.config.guild(ctx.guild).current_question()
        if current_question:
            await ctx.send(f"Current Question of the Day: {current_question}")
        else:
            await ctx.send("No question has been asked yet.")

def setup(bot):
    bot.add_cog(QotD(bot))

