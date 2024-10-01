import discord #type: ignore
from redbot.core import commands, Config #type: ignore
import random
import json
import os
from redbot.core.data_manager import bundled_data_path #type: ignore
from datetime import datetime, time, timedelta
import asyncio
import pytz #type: ignore

class FotD(commands.Cog):
    """Fact of the Day Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891)
        default_guild = {
            "enabled_categories": [],
            "current_fact": None,
            "response_count": 0,
            "fotd_channel": None,
            "fotd_time": "12:00",
            "fotd_timezone": "UTC",
            "mention_role": None,
            "last_asked": None
        }
        self.config.register_guild(**default_guild)
        self.data_path = bundled_data_path(self)
        self.categories = self.load_categories()
        self.bot.loop.create_task(self.schedule_daily_fact())

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

    async def schedule_daily_fact(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now(pytz.utc)
            for guild in self.bot.guilds:
                fotd_time_str = await self.config.guild(guild).fotd_time()
                fotd_timezone_str = await self.config.guild(guild).fotd_timezone()
                fotd_timezone = pytz.timezone(fotd_timezone_str)
                fotd_time = datetime.strptime(fotd_time_str, "%H:%M").time()
                fotd_channel_id = await self.config.guild(guild).fotd_channel()
                last_asked = await self.config.guild(guild).last_asked()
                if fotd_channel_id:
                    fotd_channel = guild.get_channel(fotd_channel_id)
                    if fotd_channel:
                        next_fotd = datetime.combine(now.date(), fotd_time)
                        next_fotd = fotd_timezone.localize(next_fotd).astimezone(pytz.utc)
                        if now > next_fotd:
                            next_fotd += timedelta(days=1)
                        if not last_asked or (now - datetime.fromisoformat(last_asked)).total_seconds() >= 86400:
                            await asyncio.sleep((next_fotd - now).total_seconds())
                            await self.post_daily_fact(fotd_channel)
                            await self.config.guild(guild).last_asked.set(next_fotd.isoformat())
            await asyncio.sleep(60)

    async def post_daily_fact(self, channel):
        guild = channel.guild
        enabled_categories = await self.config.guild(guild).enabled_categories()
        mention_role_id = await self.config.guild(guild).mention_role()
        mention_role = guild.get_role(mention_role_id) if mention_role_id else None
        if enabled_categories:
            all_facts = []
            for category in enabled_categories:
                facts = self.categories.get(category, [])
                all_facts.extend(facts)
            if all_facts:
                fact = random.choice(all_facts)
                embed = discord.Embed(
                    title="Fact of the Day",
                    description=f"Today's fact is... **{fact}**",
                    color=0xfffffe
                )
                message_content = f"{mention_role.mention}" if mention_role else ""
                allowed_mentions = discord.AllowedMentions(roles=True) if mention_role else None
                await channel.send(content=message_content, embed=embed, allowed_mentions=allowed_mentions)
                await self.config.guild(guild).current_fact.set(fact)
            else:
                await channel.send(embed=discord.Embed(
                    description="No facts available in the enabled categories.",
                    color=0xfffffe
                ))
        else:
            await channel.send(embed=discord.Embed(
                description="No categories enabled.",
                color=0xfffffe
            ))

    @commands.guild_only()
    @commands.group()
    async def fotd(self, ctx):
        """Fact of the Day commands"""

    @fotd.command()
    async def list(self, ctx):
        """List all available fact categories and their status"""
        enabled_categories = await self.config.guild(ctx.guild).enabled_categories()
        embed = discord.Embed(title="Fact categories", color=0xfffffe)
        
        if self.categories:
            total_facts = sum(len(facts) for facts in self.categories.values())
            embed.description = f"There are **{total_facts}** facts available"
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

    @fotd.command()
    async def toggle(self, ctx, category: str):
        """Toggle a fact category"""
        if category in self.categories:
            async with self.config.guild(ctx.guild).enabled_categories() as enabled_categories:
                if category in enabled_categories:
                    enabled_categories.remove(category)
                    await self.config.guild(ctx.guild).enabled_categories.set(enabled_categories)
                    await ctx.send(embed=discord.Embed(
                        description=f"Category disabled: {category}",
                        color=0xfffffe
                    ))
                else:
                    enabled_categories.append(category)
                    await self.config.guild(ctx.guild).enabled_categories.set(enabled_categories)
                    await ctx.send(embed=discord.Embed(
                        description=f"Category enabled: {category}",
                        color=0xfffffe
                    ))
        else:
            await ctx.send(embed=discord.Embed(
                description="Invalid category.",
                color=0xfffffe
            ))

    @fotd.command()
    async def enabled(self, ctx):
        """List all enabled fact categories"""
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

    @fotd.command()
    async def post(self, ctx):
        """Post a random fact of the day from enabled categories"""
        enabled_categories = await self.config.guild(ctx.guild).enabled_categories()
        if enabled_categories:
            all_facts = []
            for category in enabled_categories:
                facts = self.categories.get(category, [])
                all_facts.extend(facts)
            if all_facts:
                fact = random.choice(all_facts)
                await self.config.guild(ctx.guild).current_fact.set(fact)
                await ctx.send(embed=discord.Embed(
                    title="Fact of the Day",
                    description=fact,
                    color=0xfffffe
                ))
            else:
                await ctx.send(embed=discord.Embed(
                    description="No facts available in the enabled categories.",
                    color=0xfffffe
                ))
        else:
            await ctx.send(embed=discord.Embed(
                description="No categories enabled.",
                color=0xfffffe
            ))

    @fotd.command()
    async def current(self, ctx):
        """Show the current fact of the day"""
        current_fact = await self.config.guild(ctx.guild).current_fact()
        if current_fact:
            await ctx.send(embed=discord.Embed(
                title="Current Fact of the Day",
                description=current_fact,
                color=0xfffffe
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description="No fact has been posted yet.",
                color=0xfffffe
            ))

    @fotd.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for daily FotD"""
        await self.config.guild(ctx.guild).fotd_channel.set(channel.id)
        await ctx.send(embed=discord.Embed(
            description=f"FotD channel set to {channel.mention}",
            color=0xfffffe
        ))

    @fotd.command()
    async def settime(self, ctx, time_str: str, timezone_str: str = "UTC"):
        """Set the time and timezone for daily FotD (HH:MM in 24-hour format and timezone)"""
        known_timezones = [
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"
        ]
        try:
            datetime.strptime(time_str, "%H:%M")
            if timezone_str not in known_timezones:
                raise pytz.UnknownTimeZoneError
            await self.config.guild(ctx.guild).fotd_time.set(time_str)
            await self.config.guild(ctx.guild).fotd_timezone.set(timezone_str)
            await ctx.send(embed=discord.Embed(
                description=f"FotD time set to {time_str} in timezone {timezone_str}",
                color=0xfffffe
            ))
        except (ValueError, pytz.UnknownTimeZoneError):
            await ctx.send(embed=discord.Embed(
                description="Invalid time or timezone format. Please use HH:MM in 24-hour format and a valid timezone from the following list: " + ", ".join(known_timezones),
                color=0xfffffe
            ))

    @fotd.command()
    async def setrole(self, ctx, role: discord.Role):
        """Set the role to be mentioned for daily FotD"""
        await self.config.guild(ctx.guild).mention_role.set(role.id)
        await ctx.send(embed=discord.Embed(
            description=f"FotD mention role set to {role.mention}",
            color=0xfffffe
        ))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        fotd_channel_id = await self.config.guild(message.guild).fotd_channel()
        if message.channel.id != fotd_channel_id:
            return
        current_fact = await self.config.guild(message.guild).current_fact()
        if current_fact:
            return

