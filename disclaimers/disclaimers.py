import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class Disclaimers(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=84785745654, force_registration=True)
        self.config.register_user(disclaimers=[])
        self.predefined_disclaimers = {
            "lawyer": "⚖️ Disclaimer: This user is a lawyer, but they are not your lawyer. Any information provided is not legal advice.",
            "doctor": "🩺 Disclaimer: This user is a doctor, but they are not your doctor. Any information provided is not medical advice."
        }

    async def save_disclaimer(self, user_id: int, disclaimer: str):
        async with self.config.user_from_id(user_id).disclaimers() as disclaimers:
            disclaimers.append(disclaimer)

    async def remove_disclaimer(self, user_id: int, disclaimer: str):
        async with self.config.user_from_id(user_id).disclaimers() as disclaimers:
            if disclaimer in disclaimers:
                disclaimers.remove(disclaimer)

    async def get_disclaimers(self, user_id: int):
        return await self.config.user_from_id(user_id).disclaimers()

    @commands.group(name="disclaimers", description="Manage user disclaimers.", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def disclaimers(self, ctx: commands.Context):
        """
        Base command for managing disclaimers.
        """
        await ctx.send_help(ctx.command)

    @disclaimers.command(name="add", description="Add a disclaimer to a user.")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: commands.Context, user: discord.Member, profession: str):
        """
        Add a disclaimer to a user based on their profession.
        """
        profession = profession.lower()
        if profession not in self.predefined_disclaimers:
            await ctx.send(f"No predefined disclaimer found for profession: {profession}")
            return

        disclaimer = self.predefined_disclaimers[profession]
        await self.save_disclaimer(user.id, disclaimer)
        await ctx.send(f"Added disclaimer to {user.display_name}: {disclaimer}")

    @disclaimers.command(name="remove", description="Remove a disclaimer from a user.")
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx: commands.Context, user: discord.Member, *, profession: str):
        """
        Remove a disclaimer from a user.
        """
        profession = profession.lower()
        if profession not in self.predefined_disclaimers:
            await ctx.send(f"No predefined disclaimer found for profession: {profession}")
            return

        disclaimer = self.predefined_disclaimers[profession]
        await self.remove_disclaimer(user.id, disclaimer)
        await ctx.send(f"Removed disclaimer from {user.display_name}: {disclaimer}")

    @disclaimers.command(name="list", description="List all professions and their disclaimers.")
    @commands.has_permissions(manage_roles=True)
    async def list(self, ctx: commands.Context):
        """
        List all professions and their disclaimers, allowing users to scroll through them using reactions.
        """
        professions = list(self.predefined_disclaimers.keys())
        if not professions:
            await ctx.send("No predefined disclaimers available.")
            return

        def get_embed(page):
            profession = professions[page]
            disclaimer = self.predefined_disclaimers[profession]
            embed = discord.Embed(
                title=f"{profession.capitalize()}",
                description=f"{disclaimer}",
                colour=discord.Colour.blue()
            )
            embed.set_footer(text=f"Page {page + 1}/{len(professions)}")
            return embed

        current_page = 0
        message = await ctx.send(embed=get_embed(current_page))

        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        await message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == "➡️":
                    if current_page < len(professions) - 1:
                        current_page += 1
                        await message.edit(embed=get_embed(current_page))
                elif str(reaction.emoji) == "⬅️":
                    if current_page > 0:
                        current_page -= 1
                        await message.edit(embed=get_embed(current_page))
                elif str(reaction.emoji) == "❌":
                    await message.clear_reactions()
                    break
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break

        await message.clear_reactions()

    @disclaimers.command(name="stats", description="Show stats on how many users are assigned to each profession.")
    @commands.has_permissions(manage_roles=True)
    async def stats(self, ctx: commands.Context):
        """
        Show stats on how many users are assigned to each profession.
        """
        user_data = await self.config.all_users()
        profession_counts = {profession: 0 for profession in self.predefined_disclaimers}

        for user_id, data in user_data.items():
            for disclaimer in data.get("disclaimers", []):
                for profession, text in self.predefined_disclaimers.items():
                    if disclaimer == text:
                        profession_counts[profession] += 1

        embed = discord.Embed(
            title="Disclaimer Stats",
            colour=discord.Colour.green()
        )
        for profession, count in profession_counts.items():
            embed.add_field(name=profession.capitalize(), value=f"{count} users", inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = message.author.id
        disclaimers = await self.get_disclaimers(user_id)
        if disclaimers:
            emoji = "⚠️"
            await message.add_reaction(emoji)

            def check(reaction, user):
                return user != message.author and str(reaction.emoji) == emoji and reaction.message.id == message.id

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                return
            else:
                disclaimers_text = "\n".join(disclaimers)
                embed = discord.Embed(
                    title=f"Disclaimer for {message.author.display_name}",
                    description=disclaimers_text,
                    colour=discord.Colour.orange()
                )
                await message.channel.send(embed=embed)

async def setup(bot: Red):
    await bot.add_cog(Disclaimers(bot))


