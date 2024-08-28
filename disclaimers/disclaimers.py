import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class Disclaimers(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
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

    @commands.command(name="adddisclaimer", description="Add a disclaimer to a user.")
    @commands.has_permissions(manage_roles=True)
    async def adddisclaimer(self, ctx: commands.Context, user: discord.Member, profession: str):
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

    @commands.command(name="removedisclaimer", description="Remove a disclaimer from a user.")
    @commands.has_permissions(manage_roles=True)
    async def removedisclaimer(self, ctx: commands.Context, user: discord.Member, *, profession: str):
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


