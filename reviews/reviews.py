import csv
import discord
from redbot.core import commands, Config
from discord.ui import Button, View

class ReviewButton(discord.ui.Button):
    def __init__(self, label, review_id, style=discord.ButtonStyle.primary):
        super().__init__(label=label, style=style)
        self.review_id = review_id

    async def callback(self, interaction):
        cog = self.view.cog
        await cog.rate_review(interaction, self.review_id, int(self.label[0]))

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
                await interaction.response.send_message(f"Thank you for rating the review {rating} stars!", ephemeral=True)
            else:
                await interaction.response.send_message("Review not found.", ephemeral=True)

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

        await ctx.send("Please enter your review text:")
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            await ctx.send("You didn't enter any review. Please try again.")
            return

        content = msg.content

        view = View(timeout=None)
        for i in range(1, 6):
            view.add_item(ReviewButton(label=f"{i} Star", review_id=None))

        review_id = await self.config.guild(ctx.guild).next_id()
        async with self.config.guild(ctx.guild).reviews() as reviews:
            reviews[str(review_id)] = {"author": ctx.author.id, "content": content, "status": "pending", "rating": None}
            for item in view.children:
                item.review_id = review_id  # Assign the review ID to each button

        await self.config.guild(ctx.guild).next_id.set(review_id + 1)
        await ctx.send("Please rate your review from 1 to 5 stars:", view=view)

    @review.command(name="approve")
    @commands.has_permissions(manage_guild=True)
    async def review_approve(self, ctx, review_id: int):
        """Approve a review."""
        async with self.config.guild(ctx.guild).reviews() as reviews:
            review = reviews.get(str(review_id))
            if review and review["status"] == "pending":
                review["status"] = "approved"
                await ctx.send("The review has been approved.")
                review_channel_id = await self.config.guild(ctx.guild).review_channel()
                if review_channel_id:
                    review_channel = self.bot.get_channel(review_channel_id)
                    if review_channel:
                        embed = discord.Embed(description=f"{review['content']}\nRating: {review['rating']} stars")
                        embed.set_author(name=ctx.guild.get_member(review["author"]), icon_url=ctx.guild.get_member(review["author"]).avatar_url)
                        await review_channel.send(embed=embed)
                    else:
                        await ctx.send("Review channel not found.")
                else:
                    await ctx.send("Review channel not set.")
            else:
                await ctx.send("This review has already been handled or does not exist.")

    @review.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def review_remove(self, ctx, review_id: int):
        """Remove a review."""
        async with self.config.guild(ctx.guild).reviews() as reviews:
            if str(review_id) in reviews:
                del reviews[str(review_id)]
                await ctx.send("The review has been removed.")
            else:
                await ctx.send("Review not found.")

    @review.command(name="export")
    @commands.has_permissions(manage_guild=True)
    async def review_export(self, ctx):
        """Export reviews to a CSV file."""
        reviews = await self.config.guild(ctx.guild).reviews()
        with open(f"reviews_{ctx.guild.id}.csv", "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Author", "Content", "Status", "Rating"])
            for review_id, review in reviews.items():
                writer.writerow([review_id, ctx.guild.get_member(review["author"]), review["content"], review["status"], review.get("rating", "Not rated")])
        await ctx.send(file=discord.File(f"reviews_{ctx.guild.id}.csv"))

    @review.command(name="setchannel")
    @commands.has_permissions(manage_guild=True)
    async def review_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where approved reviews will be posted."""
        await self.config.guild(ctx.guild).review_channel.set(channel.id)
        await ctx.send(f"Review channel has been set to {channel.mention}.")

    @review.command(name="list")
    @commands.has_permissions(manage_guild=True)
    async def review_list(self, ctx):
        """List all reviews."""
        reviews = await self.config.guild(ctx.guild).reviews()
        if not reviews:
            await ctx.send("There are no reviews to list.")
            return

        for review_id, review in reviews.items():
            status = "Approved" if review["status"] == "approved" else "Pending"
            await ctx.send(f"ID: {review_id} - Status: {status}\nContent: {review['content'][:100]}... Rating: {review.get('rating', 'Not rated')}")

def setup(bot):
    bot.add_cog(ReviewsCog(bot))
