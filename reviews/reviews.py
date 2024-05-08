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

        embed = discord.Embed(description="Start by letting us know how your experience was...\n`Reply in chat with your review message`", color=discord.Color.blue())
        await ctx.send(embed=embed)
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(description="You didn't describe an experience, timed out. Please try again.", color=discord.Color.red())
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

        embed = discord.Embed(description="Please rate your experience from 1 to 5 stars:", color=discord.Color.blue())
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
                        embed = discord.Embed(
                            title="Member Review",
                            description=f"**Review Content:**\n{review['content']}\n\n**Rating:** :star:" * review['rating'],
                            color=discord.Color.gold()
                        )
                        author_member = ctx.guild.get_member(review["author"])
                        if author_member:
                            embed.set_author(name=f"Review by {author_member.display_name}", icon_url=author_member.display_avatar.url)
                            embed.set_footer(text=f"User ID: {author_member.id}")
                        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
                        embed.timestamp = datetime.datetime.utcnow()
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
        csv_filename = f"reviews_{ctx.guild.id}.csv"
        csv_file_path = os.path.join(tempfile.gettempdir(), csv_filename)
        try:
            with open(csv_file_path, "w", newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Author", "Content", "Status", "Rating"])
                for review_id, review in reviews.items():
                    author_member = ctx.guild.get_member(review["author"])
                    author_name = author_member.display_name if author_member else "Unknown"
                    writer.writerow([review_id, author_name, review["content"], review["status"], review.get("rating", "Not rated")])
            await ctx.send(file=discord.File(csv_file_path))
        except PermissionError as e:
            await ctx.send("I do not have permission to write to the file system.")
        finally:
            if os.path.exists(csv_file_path):
                os.remove(csv_file_path)

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
            embed = discord.Embed(title=f"Review ID: {review_id}", color=discord.Color.blue())
            embed.add_field(name="Status", value=status, inline=False)
            content_preview = review['content'][:100] + "..." if len(review['content']) > 100 else review['content']
            embed.add_field(name="Content", value=content_preview, inline=False)
            rating = review.get('rating', 'Not rated')
            embed.add_field(name="Rating", value=rating, inline=False)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ReviewsCog(bot))
