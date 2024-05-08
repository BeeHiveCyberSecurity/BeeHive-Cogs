import csv
import discord
import asyncio  # Added to handle the asyncio.TimeoutError
from redbot.core import commands, Config
from discord.ui import Button, View

class ReviewButton(discord.ui.Button):
    def __init__(self, label, review_id, style=discord.ButtonStyle.primary):
        super().__init__(label=label, style=style)
        self.review_id = review_id

    async def callback(self, interaction):
        cog = self.view.cog
        try:
            await cog.rate_review(interaction, self.review_id, int(self.label[0]))
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class ReviewsCog(commands.Cog):
    """A cog for managing product or service reviews."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "reviews": {},
            "review_channel": None,
            "next_id": 1
        }
        self.config.register_guild(**default_guild)

    async def rate_review(self, interaction, review_id, rating):
        async with self.config.guild(interaction.guild).reviews() as reviews:
            review = reviews.get(str(review_id))
            if review:
                review['rating'] = rating
                embed = discord.Embed(description=f"Thank you for rating the review {rating} stars!", color=discord.Color.green())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(description="Review not found.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def review(self, ctx):
        """Review commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @review.command(name="submit")
    async def review_submit(self, ctx):
        """Submit a review for approval."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        embed = discord.Embed(description="Please enter your review text:", color=discord.Color.blue())
        await ctx.send(embed=embed)
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(description="You didn't enter any review. Please try again.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        content = msg.content

        review_id = await self.config.guild(ctx.guild).next_id()
        async with self.config.guild(ctx.guild).reviews() as reviews:
            reviews[str(review_id)] = {"author": ctx.author.id, "content": content, "status": "pending", "rating": None}

        await self.config.guild(ctx.guild).next_id.set(review_id + 1)

        view = View(timeout=None)
        for i in range(1, 6):
            button = ReviewButton(label=f"{i} Star", review_id=review_id)
            view.add_item(button)
        view.cog = self  # Assign the cog reference to the view for callback access

        embed = discord.Embed(description="Please rate your review from 1 to 5 stars:", color=discord.Color.blue())
        message = await ctx.send(embed=embed, view=view)
        await view.wait()  # Wait for the interaction to be completed

        if not view.children:  # If the view has no children, the interaction was completed
            embed = discord.Embed(description="Thank you for submitting your review!", color=discord.Color.green())
            await message.edit(embed=embed, view=None)
        else:
            embed = discord.Embed(description="Review rating was not received. Please try submitting again.", color=discord.Color.red())
            await message.edit(embed=embed, view=None)
            
    @review.command(name="approve")
    @commands.has_permissions(manage_guild=True)
    async def review_approve(self, ctx, review_id: int):
        """Approve a review."""
        async with self.config.guild(ctx.guild).reviews() as reviews:
            review = reviews.get(str(review_id))
            if review and review["status"] == "pending":
                review["status"] = "approved"
                embed = discord.Embed(description="The review has been approved.", color=discord.Color.green())
                await ctx.send(embed=embed)
                review_channel_id = await self.config.guild(ctx.guild).review_channel()
                if review_channel_id:
                    review_channel = self.bot.get_channel(review_channel_id)
                    if review_channel:
                        embed = discord.Embed(description=f"{review['content']}\nRating: {review['rating']} stars", color=discord.Color.blue())
                        author_member = ctx.guild.get_member(review["author"])
                        if author_member:
                            embed.set_author(name=author_member, icon_url=author_member.avatar_url)
                        await review_channel.send(embed=embed)
                    else:
                        embed = discord.Embed(description="Review channel not found.", color=discord.Color.red())
                        await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description="Review channel not set.", color=discord.Color.red())
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description="This review has already been handled or does not exist.", color=discord.Color.red())
                await ctx.send(embed=embed)

    @review.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def review_remove(self, ctx, review_id: int):
        """Remove a review."""
        async with self.config.guild(ctx.guild).reviews() as reviews:
            if str(review_id) in reviews:
                del reviews[str(review_id)]
                embed = discord.Embed(description="The review has been removed.", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description="Review not found.", color=discord.Color.red())
                await ctx.send(embed=embed)

    @review.command(name="export")
    @commands.has_permissions(manage_guild=True)
    async def review_export(self, ctx):
        """Export reviews to a CSV file."""
        reviews = await self.config.guild(ctx.guild).reviews()
        with open(f"reviews_{ctx.guild.id}.csv", "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Author", "Content", "Status", "Rating"])
            for review_id, review in reviews.items():
                author_member = ctx.guild.get_member(review["author"])
                writer.writerow([review_id, author_member, review["content"], review["status"], review.get("rating", "Not rated")])
        await ctx.send(file=discord.File(f"reviews_{ctx.guild.id}.csv"))

    @review.command(name="setchannel")
    @commands.has_permissions(manage_guild=True)
    async def review_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where approved reviews will be posted."""
        await self.config.guild(ctx.guild).review_channel.set(channel.id)
        embed = discord.Embed(description=f"Review channel has been set to {channel.mention}.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @review.command(name="list")
    @commands.has_permissions(manage_guild=True)
    async def review_list(self, ctx):
        """List all reviews."""
        reviews = await self.config.guild(ctx.guild).reviews()
        if not reviews:
            embed = discord.Embed(description="There are no reviews to list.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        for review_id, review in reviews.items():
            status = "Approved" if review["status"] == "approved" else "Pending"
            embed = discord.Embed(description=f"ID: {review_id} - Status: {status}\nContent: {review['content'][:100]}... Rating: {review.get('rating', 'Not rated')}", color=discord.Color.blue())
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ReviewsCog(bot))
