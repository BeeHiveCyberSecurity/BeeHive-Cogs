import discord
import asyncio
from redbot.core import commands

class Offers(commands.Cog):
    """A cog to browse money-saving offers."""

    def __init__(self, bot):
        self.bot = bot
        self.offers_data = {
            "Adult": [
                {"title": "Puffco", "description": "Puffco offers innovative products designed to enhance the experience of using concentrates. Our focus is on elegance, simplicity, and providing a comprehensive sensory experience. Discover new flavors, sensations, and mental clarity with Puffco's unique approach.", "offer": "$30 off valid for first-time Puffco customers only, $150 cart minimum. Cart must include a Pivot, Peak, Proxy, Peak Pro or Plus. This offer does not apply to new products within the first 30 days of their release. Discount codes cannot stack.", "link": "http://rwrd.io/wu0i3ir?c", "logo": "https://cdn.brandfetch.io/idD9NYRknz/w/2000/h/3478/theme/dark/logo.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x000000}
            ],
            "Business": [
                {"title": "OpenPhone", "description": "OpenPhone is a modern business phone system that integrates calls, texts, and contacts into a collaborative workspace. It helps businesses build stronger customer relationships with features like shared numbers, AI, and automations. OpenPhone is designed to streamline communication and enhance team collaboration.", "offer": "Sign up for OpenPhone using the link below and remain a paying customer for three (3) months. You'll get a $20 Visa gift card as a reward.", "link": "https://openph.one/referral/14OYE-r", "logo": "https://cdn.brandfetch.io/id8eCYh_qw/w/800/h/582/theme/dark/symbol.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x6439F5},
                {"title": "Akamai", "description": "Akamai provides a cloud computing platform and edge network that ensures performance, reliability, and security for businesses worldwide. Their services are designed to meet the demands of modern digital enterprises, offering solutions for content delivery, cybersecurity, and cloud computing. Akamai's extensive network helps businesses operate efficiently across the globe.", "offer": "Sign up using the link below and you'll receive a $100, 60-day credit towards managed databases, clusters, virtual machines, and more once a valid payment method is added to your new account.", "link": "https://www.linode.com/lp/refer/?r=577180eb1019c3b67e5f5d732b5d66a2c5727fe9", "logo": "https://cdn.brandfetch.io/idGtBgBpqB/w/800/h/870/theme/dark/symbol.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0x017AC6},
                {"title": "Brex", "description": "Brex is a financial technology company that provides business credit cards and cash management accounts tailored for startups. Their services are designed to help new businesses manage finances efficiently and access credit without personal guarantees. Brex aims to simplify financial operations for growing companies.", "offer": "Sign up for Brex using the link below and get a $500 gift card when you spend $8,000 in your first month.", "link": "https://brex.com/signup?rc=ET0xAhr", "logo": "https://cdn.brandfetch.io/idu49Dl4i8/w/800/h/643/theme/dark/idKagHeH6-.png?c=1dxbfHSJFAPEGdCLU4o5B", "color": 0xf46a35}
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
                embed = discord.Embed(title=offer["title"], description=f"{offer['description']}\n\n**{offer['offer']}**", color=offer["color"])
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
