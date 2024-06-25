import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class JoinMaster(commands.Cog):
    """Cog to join servers on behalf of users using OAuth2"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "client_id": "",
            "client_secret": "",
            "redirect_uri": "",
            "scopes": ["bot", "identify", "guilds.join"]
        }
        self.config.register_global(**default_global)

    @commands.group()
    async def joinmaster(self, ctx: commands.Context):
        """Group command for JoinMaster settings"""
        pass

    @joinmaster.command()
    async def set_credentials(self, ctx: commands.Context, client_id: str, client_secret: str, redirect_uri: str):
        """Set the OAuth2 credentials"""
        await self.config.client_id.set(client_id)
        await self.config.client_secret.set(client_secret)
        await self.config.redirect_uri.set(redirect_uri)
        await ctx.send("OAuth2 credentials have been set.")

    @commands.command()
    async def authorize(self, ctx: commands.Context):
        """Generate an OAuth2 URL for authorization"""
        client_id = await self.config.client_id()
        redirect_uri = await self.config.redirect_uri()
        scopes = await self.config.scopes()

        if not client_id or not redirect_uri:
            await ctx.send("OAuth2 credentials are not set. Please set them using the joinmaster set_credentials command.")
            return

        oauth_url = (
            f"https://discord.com/api/oauth2/authorize?client_id={client_id}"
            f"&redirect_uri={redirect_uri}&response_type=code&scope={' '.join(scopes)}"
        )
        await ctx.send(f"Please authorize the bot using this URL: {oauth_url}")

    @commands.command()
    async def forcejoin(self, ctx: commands.Context, invite: str, code: str):
        """Forcefully join a server using an invite link and authorization code"""
        client_id = await self.config.client_id()
        client_secret = await self.config.client_secret()
        redirect_uri = await self.config.redirect_uri()
        scopes = await self.config.scopes()

        if not client_id or not client_secret or not redirect_uri:
            await ctx.send("OAuth2 credentials are not set. Please set them using the joinmaster set_credentials command.")
            return

        token_url = "https://discord.com/api/oauth2/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes)
        }

        async with self.bot.session.post(token_url, data=data) as resp:
            if resp.status != 200:
                await ctx.send("Failed to retrieve access token.")
                return
            token_info = await resp.json()

        access_token = token_info.get("access_token")
        if not access_token:
            await ctx.send("Failed to retrieve access token.")
            return

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        join_url = f"https://discord.com/api/v9/invites/{invite}"
        async with self.bot.session.post(join_url, headers=headers) as resp:
            if resp.status == 200:
                await ctx.send("Successfully joined the server.")
            else:
                await ctx.send("Failed to join the server.")

def setup(bot: Red):
    bot.add_cog(JoinMaster(bot))
