import discord
from discord.ext import commands
import aiohttp

class Weather(commands.Cog):
    """Weather information from weather.gov"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def weather(self, ctx, location: str):
        """Get the current weather for a location from weather.gov"""
        async with self.session.get(f"https://api.weather.gov/points/{location}") as response:
            if response.status != 200:
                await ctx.send("Could not retrieve weather data.")
                return

            data = await response.json()
            forecast_url = data['properties']['forecast']
            alerts_url = data['properties']['alerts']

            async with self.session.get(forecast_url) as forecast_response:
                if forecast_response.status != 200:
                    await ctx.send("Could not retrieve forecast data.")
                    return

                forecast_data = await forecast_response.json()
                periods = forecast_data['properties']['periods']
                current_period = periods[0]

                embed = discord.Embed(
                    title=f"Weather for {location}",
                    description=current_period['detailedForecast'],
                    color=discord.Color.blue()
                )
                embed.add_field(name="Temperature", value=f"{current_period['temperature']} {current_period['temperatureUnit']}")
                embed.add_field(name="Wind", value=current_period['windSpeed'])
                embed.add_field(name="Wind Direction", value=current_period['windDirection'])
                embed.set_thumbnail(url=current_period['icon'])

                # Check for alerts
                async with self.session.get(alerts_url) as alerts_response:
                    if alerts_response.status == 200:
                        alerts_data = await alerts_response.json()
                        alerts = alerts_data['features']
                        if alerts:
                            alert_messages = [alert['properties']['headline'] for alert in alerts]
                            embed.add_field(name="Alerts", value="\n".join(alert_messages), inline=False)

                await ctx.send(embed=embed)


