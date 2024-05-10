
import aiohttp
import discord #type: ignore
from redbot.core import Config, commands

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  
        self.api_url = "https://api.weather.com/v3/wx/conditions/current"
        self.config.register_global(api_key="")

    async def cog_unload(self):
        if hasattr(self, '_http_client'):
            await self._http_client.close()

    async def _make_request(self, url):
        if not hasattr(self, '_http_client'):
            self._http_client = aiohttp.ClientSession()
        try:
            async with self._http_client.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error making request: {e}")
            return None

    @commands.command()
    async def weather(self, ctx, *, location: str):
        """Fetches the current weather for a given location."""
        api_key = await self.config.api_key()
        url = f"{self.api_url}?apiKey={api_key}&format=json&language=en-US&location={location}"
        response = await self._make_request(url)
        if response:
            embed = discord.Embed(title=f"Weather for {location}", color=discord.Color.blue())
            embed.add_field(name="Temperature", value=f"{response['imperial']['temp']}°F", inline=True)
            embed.add_field(name="Feels Like", value=f"{response['imperial']['feelslike']}°F", inline=True)
            embed.add_field(name="Humidity", value=f"{response['humidity']}%", inline=True)
            embed.add_field(name="Wind", value=f"{response['wspd']} mph {response['wdir']['dir']}", inline=True)
            embed.add_field(name="Visibility", value=f"{response['imperial']['vis']} miles", inline=True)
            embed.add_field(name="Pressure", value=f"{response['imperial']['mslp']} inHg", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error fetching weather data.")

