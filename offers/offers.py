import discord
import asyncio
from redbot.core import commands

class Offers(commands.Cog):
    """A cog to browse money-saving offers."""

    def __init__(self, bot):
        self.bot = bot
        self.offers_data = {
            "Electronics": [
                {"title": "Discount on Laptops", "description": "Save 20% on select laptops.", "link": "http://example.com/laptops", "logo": "http://example.com/laptop_logo.png"},
                {"title": "Smartphone Sale", "description": "Get the latest smartphones at a discount.", "link": "http://example.com/smartphones", "logo": "http://example.com/smartphone_logo.png"}
            ],
            "Fashion": [
                {"title": "Summer Collection Sale", "description": "Up to 50% off on summer collection.", "link": "http://example.com/summer", "logo": "http://example.com/summer_logo.png"},
                {"title": "Winter Wear Deals", "description": "Exclusive discounts on winter wear.", "link": "http://example.com/winter", "logo": "http://example.com/winter_logo.png"}
            ],
            "Groceries": [
                {"title": "Weekly Grocery Discounts", "description": "Save on your weekly grocery shopping.", "link": "http://example.com/groceries", "logo": "http://example.com/groceries_logo.png"},
                {"title": "Organic Food Offers", "description": "Discounts on organic food items.", "link": "http://example.com/organic", "logo": "http://example.com/organic_logo.png"}
            ]
        }

    @commands.command()
    async def offers(self, ctx):
        """Browse different categories of money-saving offers."""
        select = discord.ui.Select(placeholder="Choose a category", min_values=1, max_values=1)

        for category in self.offers_data.keys():
            select.add_option(label=category, value=category)

        async def select_callback(interaction):
            selected_category = select.values[0]
            offers = self.offers_data[selected_category]
            current_index = 0

            async def update_embed(index):
                offer = offers[index]
                embed = discord.Embed(title=offer["title"], description=f"{offer['description']}\n[Link]({offer['link']})", color=0x00ff00)
                embed.set_thumbnail(url=offer["logo"])
                embed.set_footer(text=f"Offer {index + 1} of {len(offers)}")
                return embed

            async def interaction_check(interaction):
                return interaction.user == ctx.author

            embed = await update_embed(current_index)
            message = await interaction.response.edit_message(embed=embed)

            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "➡️":
                        current_index = (current_index + 1) % len(offers)
                    elif str(reaction.emoji) == "⬅️":
                        current_index = (current_index - 1) % len(offers)

                    embed = await update_embed(current_index)
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)

                except asyncio.TimeoutError:
                    break

        select.callback = select_callback
        view = discord.ui.View(timeout=None)
        view.add_item(select)

        initial_embed = discord.Embed(title="Browse Offers", description="Select a category to view offers.", color=0x00ff00)
        await ctx.send(embed=initial_embed, view=view)
