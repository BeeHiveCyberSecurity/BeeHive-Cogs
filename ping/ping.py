import discord  # type: ignore
import speedtest  # type: ignore
from redbot.core import commands  # Import Red's commands

class Ping(commands.Cog):  # Use Red's Cog class
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", description="Displays the bot's latency and additional diagnostic information.")
    async def ping(self, ctx: commands.Context):
        await ctx.defer()

        latency = self.bot.latency
        heartbeat_latency = round(latency * 1000, 2)
        ws_latency = round(self.bot.latency * 1000, 2)

        if not hasattr(self, 'latency_history'):
            self.latency_history = []
        self.latency_history.append(ws_latency)
        if len(self.latency_history) > 5:
            self.latency_history.pop(0)
        avg_latency = round(sum(self.latency_history) / len(self.latency_history), 2)

        async with ctx.typing():
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()
            download_speed = round(st.download() / 1_000_000, 2)
            upload_speed = round(st.upload() / 1_000_000, 2)
            ping = st.results.ping

            # Retry logic for high latency
            retries = 0
            max_retries = 3
            while ping > 250 and retries < max_retries:  # Adjust threshold as needed
                st.get_best_server()
                download_speed = round(st.download() / 1_000_000, 2)
                upload_speed = round(st.upload() / 1_000_000, 2)
                ping = st.results.ping
                retries += 1

            if ping > 250:  # If still high after retries
                await ctx.send("Network conditions are currently fluctuating too much to measure conditions accurately. Please try again later.")
                return

        if avg_latency > 100:  # Adjust thresholds as needed
            embed_color = discord.Color(0xff4545)
            embed_title = "Connection impacted"
        else:
            embed_color = discord.Color(0x2bbd8e)
            embed_title = "Connection OK"

        # Create an embed for a more detailed response
        embed = discord.Embed(title=embed_title, color=embed_color)
        embed.add_field(name="Averaged latency", value=f"{avg_latency}ms", inline=True)
        embed.add_field(name="Backbone latency", value=f"{ping} ms", inline=True)
        embed.add_field(name="", value="\u200b", inline=False)
        embed.add_field(name="Download speed", value=f"{download_speed} Mbps", inline=True)
        embed.add_field(name="Upload speed", value=f"{upload_speed} Mbps", inline=True)

        await ctx.send(embed=embed)