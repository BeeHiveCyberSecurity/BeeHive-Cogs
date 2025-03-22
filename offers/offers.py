import discord
from redbot.core import commands

class Offers(commands.Cog):
    """A cog to browse money-saving offers."""

    def __init__(self, bot):
        self.bot = bot
        self.offers_data = {
            "Electronics": [
                {"title": "Discount on Laptops", "description": "Save 20% on select laptops.", "link": "http://example.com/laptops"},
                {"title": "Smartphone Sale", "description": "Get the latest smartphones at a discount.", "link": "http://example.com/smartphones"}
            ],
            "Fashion": [
                {"title": "Summer Collection Sale", "description": "Up to 50% off on summer collection.", "link": "http://example.com/summer"},
                {"title": "Winter Wear Deals", "description": "Exclusive discounts on winter wear.", "link": "http://example.com/winter"}
            ],
            "Groceries": [
                {"title": "Weekly Grocery Discounts", "description": "Save on your weekly grocery shopping.", "link": "http://example.com/groceries"},
                {"title": "Organic Food Offers", "description": "Discounts on organic food items.", "link": "http://example.com/organic"}
            ]
        }

    @commands.command()
    async def offers(self, ctx):
        """Browse different categories of money-saving offers."""
        view = discord.ui.View()
        select = discord.ui.Select(placeholder="Choose a category", min_values=1, max_values=1)

        for category in self.offers_data.keys():
            select.add_option(label=category, value=category)

        async def select_callback(interaction):
            selected_category = select.values[0]
            offers = self.offers_data[selected_category]
            embed = discord.Embed(title=f"{selected_category} Offers", color=0x00ff00)

            for offer in offers:
                embed.add_field(name=offer["title"], value=f"{offer['description']}\n[Link]({offer['link']})", inline=False)

            await interaction.response.edit_message(embed=embed)

        select.callback = select_callback
        view.add_item(select)

        initial_embed = discord.Embed(title="Browse Offers", description="Select a category to view offers.", color=0x00ff00)
        await ctx.send(embed=initial_embed, view=view)
