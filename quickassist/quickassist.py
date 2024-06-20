
import discord #type: ignore
from discord.ext import commands #type: ignore

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='powerrole')
    @commands.has_permissions(administrator=True)
    async def create_power_role(self, ctx):
        guild = ctx.guild
        member = ctx.author

        # Define the role permissions
        bot_member = guild.get_member(self.bot.user.id)
        permissions = discord.Permissions.none()
        
        # Check each permission the bot has and add it to the role permissions
        for perm, value in bot_member.guild_permissions:
            if value:
                setattr(permissions, perm, True)

        # Create the role
        role = await guild.create_role(name="PowerRole", permissions=permissions)

        # Move the role as high as possible
        await role.edit(position=len(guild.roles) - 1)

        # Add the role to the user
        await member.add_roles(role)

        await ctx.send(f"Role `{role.name}` created and assigned to {member.mention}.")

def setup(bot):
    bot.add_cog(RoleManager(bot))
