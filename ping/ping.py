import discord  #type: ignore
import speedtest  #type: ignore
from redbot.core import commands #type: ignore
import asyncio
from concurrent.futures import ThreadPoolExecutor

class Ping(commands.Cog):  # Use Red's Cog class
    def __init__(self, bot):
        self.bot = bot
        self.executor = ThreadPoolExecutor(max_workers=1)

    @commands.command(name="ping", description="Displays the bot's latency and additional diagnostic information.")
    async def ping(self, ctx: commands.Context):
        await ctx.defer()
        ws_latency = round(self.bot.latency * 1000, 2)

        if not hasattr(self, 'latency_history'):
            self.latency_history = []
        self.latency_history.append(ws_latency)
        if len(self.latency_history) > 5:
            self.latency_history.pop(0)
        avg_latency = round(sum(self.latency_history) / len(self.latency_history), 2)

        async with ctx.typing():
            try:
                download_speed, upload_speed, ping = await asyncio.get_event_loop().run_in_executor(self.executor, self.run_speedtest)
            except Exception as e:
                await ctx.send(f"An error occurred while performing the speed test: {e}")
                return

            if ping > 250:  # If still high after retries
                await ctx.send("Network conditions are currently fluctuating too much to measure conditions accurately. Please try again later.")
                return

        if avg_latency > 100:  # Adjust thresholds as needed
            embed_color = discord.Color(0xff4545)
            embed_title = "Connection impacted"
            embed_description = "Need better bot performance? Consider upgrading to a dedicated server for optimal performance. [Here's $100 on us to try out dedicated hosting with Linode](https://www.linode.com/lp/refer/?r=577180eb1019c3b67e5f5d732b5d66a2c5727fe9)"
        else:
            embed_color = discord.Color(0x2bbd8e)
            embed_title = "Connection OK"
            embed_description = "Your connection is stable and performing well for bot operations."

        # Create an embed for a more detailed response
        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="Latency", value="\u200b", inline=False)
        embed.add_field(name="Network latency", value=f"**{avg_latency}ms**", inline=True)
        embed.add_field(name="Host latency", value=f"**{ping}ms**", inline=True)
        embed.add_field(name="Speedtest", value="\u200b", inline=False)
        embed.add_field(name="Download speed", value=f"**{download_speed}Mbps**", inline=True)
        embed.add_field(name="Upload speed", value=f"**{upload_speed}Mbps**", inline=True)

        await ctx.send(embed=embed)

    def run_speedtest(self):
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

        return download_speed, upload_speed, ping