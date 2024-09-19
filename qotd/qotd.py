import discord
from redbot.core import commands, Config
import random
import json
import os
from redbot.core.data_manager import bundled_data_path
from datetime import datetime, time, timedelta
import asyncio

class QotD(commands.Cog):
    """Question of the Day Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled_categories": [],
            "current_question": None,
            "response_count": 0,
            "qotd_channel": None,
            "qotd_time": "12:00"
        }
        self.config.register_guild(**default_guild)
        self.data_path = bundled_data_path(self)
        self.categories = self.load_categories()
        self.bot.loop.create_task(self.schedule_daily_question())

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

    async def schedule_daily_question(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now()
            for guild in self.bot.guilds:
                qotd_time_str = await self.config.guild(guild).qotd_time()
                qotd_time = datetime.strptime(qotd_time_str, "%H:%M").time()
                qotd_channel_id = await self.config.guild(guild).qotd_channel()
                if qotd_channel_id:
                    qotd_channel = guild.get_channel(qotd_channel_id)
                    if qotd_channel:
                        next_qotd = datetime.combine(now.date(), qotd_time)
                        if now.time() > qotd_time:
                            next_qotd += timedelta(days=1)
                        await asyncio.sleep((next_qotd - now).total_seconds())
                        await self.ask_daily_question(qotd_channel)
            await asyncio.sleep(60)

    async def ask_daily_question(self, channel):
        guild = channel.guild
        enabled_categories = await self.config.guild(guild).enabled_categories()
        if enabled_categories:
            questions = []
            for category in enabled_categories:
                questions.extend(self.categories.get(category, []))
            if questions:
                question = random.choice(questions)
                response_count = await self.config.guild(guild).response_count()
                embed = discord.Embed(
                    title="Question of the Day",
                    description=f"Yesterday's question received {response_count} responses.\n\nQuestion: {question}",
                    color=0xfffffe
                )
                await channel.send(embed=embed)
                await self.config.guild(guild).response_count.set(0)
                await self.config.guild(guild).current_question.set(question)
            else:
                await channel.send(embed=discord.Embed(
                    description="No questions available in the enabled categories.",
                    color=0xfffffe
                ))
        else:
            await channel.send(embed=discord.Embed(
                description="No categories enabled.",
                color=0xfffffe
            ))

    @commands.guild_only()
    @commands.group()
    async def qotd(self, ctx):
        """Question of the Day commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @qotd.command()
    async def list(self, ctx):
        """List all available question categories and their status"""
        enabled_categories = await self.config.guild(ctx.guild).enabled_categories()
        embed = discord.Embed(title="Question categories", color=0xfffffe)
        
        if self.categories:
            total_questions = sum(len(questions) for questions in self.categories.values())
            embed.description = f"There are **{total_questions}** questions available"
            for category in self.categories.keys():
                capitalized_category = category.capitalize()
                status = "Enabled" if category in enabled_categories else "Disabled"
                embed.add_field(name=capitalized_category, value=status, inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(
                description="No categories available.",
                color=0xfffffe
            ))

    @qotd.command()
    async def toggle(self, ctx, category: str):
        """Toggle a question category"""
        if category in self.categories:
            async with self.config.guild(ctx.guild).enabled_categories() as enabled_categories:
                if category in enabled_categories:
                    enabled_categories.remove(category)
                    await ctx.send(embed=discord.Embed(
                        description=f"Category disabled: {category}",
                        color=0xfffffe
                    ))
                else:
                    enabled_categories.append(category)
                    await ctx.send(embed=discord.Embed(
                        description=f"Category enabled: {category}",
                        color=0xfffffe
                    ))
        else:
            await ctx.send(embed=discord.Embed(
                description="Invalid category.",
                color=0xfffffe
            ))

    @qotd.command()
    async def enabled(self, ctx):
        """List all enabled question categories"""
        enabled_categories = await self.config.guild(ctx.guild).enabled_categories()
        if enabled_categories:
            category_list = "\n".join(enabled_categories)
            await ctx.send(embed=discord.Embed(
                title="Enabled Categories",
                description=category_list,
                color=0xfffffe
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description="No categories enabled.",
                color=0xfffffe
            ))

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
                await ctx.send(embed=discord.Embed(
                    title="Question of the Day",
                    description=question,
                    color=0xfffffe
                ))
            else:
                await ctx.send(embed=discord.Embed(
                    description="No questions available in the enabled categories.",
                    color=0xfffffe
                ))
        else:
            await ctx.send(embed=discord.Embed(
                description="No categories enabled.",
                color=0xfffffe
            ))

    @qotd.command()
    async def current(self, ctx):
        """Show the current question of the day"""
        current_question = await self.config.guild(ctx.guild).current_question()
        if current_question:
            await ctx.send(embed=discord.Embed(
                title="Current Question of the Day",
                description=current_question,
                color=0xfffffe
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description="No question has been asked yet.",
                color=0xfffffe
            ))

    @qotd.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for daily QotD"""
        await self.config.guild(ctx.guild).qotd_channel.set(channel.id)
        await ctx.send(embed=discord.Embed(
            description=f"QotD channel set to {channel.mention}",
            color=0xfffffe
        ))

    @qotd.command()
    async def settime(self, ctx, time_str: str):
        """Set the time for daily QotD (HH:MM in 24-hour format)"""
        try:
            datetime.strptime(time_str, "%H:%M")
            await self.config.guild(ctx.guild).qotd_time.set(time_str)
            await ctx.send(embed=discord.Embed(
                description=f"QotD time set to {time_str}",
                color=0xfffffe
            ))
        except ValueError:
            await ctx.send(embed=discord.Embed(
                description="Invalid time format. Please use HH:MM in 24-hour format.",
                color=0xfffffe
            ))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        current_question = await self.config.guild(message.guild).current_question()
        if current_question and current_question in message.content:
            async with self.config.guild(message.guild).response_count() as response_count:
                response_count += 1


