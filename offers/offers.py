import discord
import asyncio
from redbot.core import commands

class Offers(commands.Cog):
    """A cog to browse money-saving offers."""

    def __init__(self, bot):
        self.bot = bot
        self.offers_data = {
            "Electronics": [
                {"title": "Discount on Laptops", "description": "High-performance laptops for work and play.", "offer": "Save 20% on select laptops.", "link": "http://example.com/laptops", "logo": "http://example.com/laptop_logo.png", "color": 0x1f8b4c},
                {"title": "Smartphone Sale", "description": "Latest smartphones with cutting-edge features.", "offer": "Get the latest smartphones at a discount.", "link": "http://example.com/smartphones", "logo": "http://example.com/smartphone_logo.png", "color": 0x3498db}
            ],
            "Fashion": [
                {"title": "Summer Collection Sale", "description": "Trendy summer outfits for all occasions.", "offer": "Up to 50% off on summer collection.", "link": "http://example.com/summer", "logo": "http://example.com/summer_logo.png", "color": 0xe74c3c},
                {"title": "Winter Wear Deals", "description": "Stay warm with our stylish winter wear.", "offer": "Exclusive discounts on winter wear.", "link": "http://example.com/winter", "logo": "http://example.com/winter_logo.png", "color": 0x9b59b6}
            ],
            "Groceries": [
                {"title": "Weekly Grocery Discounts", "description": "Fresh groceries delivered to your door.", "offer": "Save on your weekly grocery shopping.", "link": "http://example.com/groceries", "logo": "http://example.com/groceries_logo.png", "color": 0x2ecc71},
                {"title": "Organic Food Offers", "description": "Healthy organic food for a better lifestyle.", "offer": "Discounts on organic food items.", "link": "http://example.com/organic", "logo": "http://example.com/organic_logo.png", "color": 0xf1c40f}
            ],
            "Business": [
                {"title": "OpenPhone", "description": "OpenPhone brings your calls, texts, and contacts into a collaborative workspace. Build stronger customer relationships and respond faster with shared numbers, AI, and automations.", "offer": "Sign up for OpenPhone using the link below and remain a paying customer for three (3) months. You'll get a $20 Visa gift card as a reward.", "link": "https://openph.one/referral/14OYE-r", "logo": "https://cdn.brandfetch.io/id8eCYh_qw/w/800/h/582/theme/dark/symbol.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x6439F5}
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
                embed = discord.Embed(title=offer["title"], description=f"**{offer['description']}**\n\n{offer['offer']}", color=offer["color"])
                embed.set_thumbnail(url=offer["logo"])
                embed.set_footer(text=f"Offer {index + 1} of {len(offers)}")
                return embed

            async def interaction_check(interaction):
                return interaction.user == ctx.author

            embed = await update_embed(current_index)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label=f"View {offers[current_index]['title']}", url=offers[current_index]["link"]))
            message = await interaction.response.edit_message(embed=embed, view=view)

            if len(offers) > 1:
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
                        view = discord.ui.View(timeout=None)
                        view.add_item(discord.ui.Button(label=f"View {offers[current_index]['title']}", url=offers[current_index]["link"]))
                        await message.edit(embed=embed, view=view)
                        await message.remove_reaction(reaction, user)

                    except asyncio.TimeoutError:
                        break

        select.callback = select_callback
        view = discord.ui.View(timeout=None)
        view.add_item(select)

        initial_embed = discord.Embed(title="Browse Offers", description="Select a category to view offers.", color=0x00ff00)
        await ctx.send(embed=initial_embed, view=view)
