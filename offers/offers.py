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
            "Adult": [
                {"title": "Puffco", "description": "Puffco products are a platform for the plant to shine and make the magic of concentrates accessible to everyone. We strive for elegance, simplicity and delivering the full spectrum experience. Whether it’s the flavor nuances you haven’t noticed before in your favorite strains, the new feelings in your body, and/ or a clearer mental state - the Puffco difference is profound.", "offer": "$30 off valid for first-time Puffco customers only, $150 cart minimum. Cart must include a Pivot, Peak, Proxy, Peak Pro or Plus. This offer does not apply to new products within the first 30 days of their release. Discount codes cannot stack.", "link": "http://rwrd.io/wu0i3ir?c", "logo": "https://cdn.brandfetch.io/idD9NYRknz/w/2000/h/3478/theme/dark/logo.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x000000}
            ],
            "Business": [
                {"title": "OpenPhone", "description": "OpenPhone brings your calls, texts, and contacts into a collaborative workspace. Build stronger customer relationships and respond faster with shared numbers, AI, and automations.", "offer": "Sign up for OpenPhone using the link below and remain a paying customer for three (3) months. You'll get a $20 Visa gift card as a reward.", "link": "https://openph.one/referral/14OYE-r", "logo": "https://cdn.brandfetch.io/id8eCYh_qw/w/800/h/582/theme/dark/symbol.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x6439F5},
                {"title": "Akamai", "description": "Everywhere you do business, Akamai is there. Get the performance, reliability, and security your business demands with the world’s most distributed cloud computing platform and edge network.", "offer": "Sign up using the link below and you'll receive a $100, 60-day credit towards managed databases, clusters, virtual machines, and more once a valid payment method is added to your new account.", "link": "https://www.linode.com/lp/refer/?r=577180eb1019c3b67e5f5d732b5d66a2c5727fe9", "logo": "https://cdn.brandfetch.io/idGtBgBpqB/w/800/h/870/theme/dark/symbol.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x017AC6}
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

            # Delete the original message with the select menu
            await interaction.message.delete()

            # Send a new message with the first offer
            embed = await update_embed(current_index)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label=f"View {offers[current_index]['title']}", url=offers[current_index]["link"]))
            message = await ctx.send(embed=embed, view=view)

            if len(offers) > 1:
                left_button = discord.ui.Button(emoji="⬅️", style=discord.ButtonStyle.secondary)
                right_button = discord.ui.Button(emoji="➡️", style=discord.ButtonStyle.secondary)

                async def left_button_callback(interaction):
                    nonlocal current_index
                    current_index = (current_index - 1) % len(offers)
                    embed = await update_embed(current_index)
                    view = discord.ui.View(timeout=None)
                    view.add_item(discord.ui.Button(label=f"View {offers[current_index]['title']}", url=offers[current_index]["link"]))
                    view.add_item(left_button)
                    view.add_item(right_button)
                    await message.edit(embed=embed, view=view)
                    await interaction.response.defer()  # Acknowledge the interaction to prevent "interaction failed"

                async def right_button_callback(interaction):
                    nonlocal current_index
                    current_index = (current_index + 1) % len(offers)
                    embed = await update_embed(current_index)
                    view = discord.ui.View(timeout=None)
                    view.add_item(discord.ui.Button(label=f"View {offers[current_index]['title']}", url=offers[current_index]["link"]))
                    view.add_item(left_button)
                    view.add_item(right_button)
                    await message.edit(embed=embed, view=view)
                    await interaction.response.defer()  # Acknowledge the interaction to prevent "interaction failed"

                left_button.callback = left_button_callback
                right_button.callback = right_button_callback

                view.add_item(left_button)
                view.add_item(right_button)

                await message.edit(view=view)  # Ensure the view is updated with buttons

        select.callback = select_callback
        view = discord.ui.View(timeout=None)
        view.add_item(select)

        initial_embed = discord.Embed(title="Browse available offers", description="Select a category to view offers. Some offers may be time-sensitive, or unavailable in specific regions.", color=0xfffffe)
        await ctx.send(embed=initial_embed, view=view)
