import discord  # type: ignore
import datetime  # type: ignore
import speedtest  # type: ignore
from redbot.core import commands  # type: ignore
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.latency_history = []
        self.speedtest_results = []  # Store speedtest results

    @commands.hybrid_command(name="ping", description="Displays the bot's latency, download speed, and upload speed")
    async def ping(self, ctx: commands.Context):
        """Displays the bot's latency, download speed, and upload speed"""
        await ctx.defer()
        ws_latency = round(self.bot.latency * 1000, 2)

        self._update_latency_history(ws_latency)
        avg_latency = self._calculate_average_latency()

        embed = self._create_initial_embed(avg_latency)
        initial_message = await ctx.send(embed=embed)

        try:
            download_speed, upload_speed, ping = await self._perform_speedtest()
            self._log_speedtest_result(download_speed, upload_speed, ping)  # Log the result
        except Exception as e:
            await initial_message.edit(content=f"An error occurred while performing the speed test: {e}", embed=None)
            return

        if ping > 250:
            await initial_message.edit(content="Network conditions are currently fluctuating too much to measure conditions accurately. Please try again later.", embed=None)
            return

        embed = await self._create_final_embed(avg_latency, download_speed, upload_speed, ping)
        await initial_message.edit(embed=embed)

    @commands.hybrid_command(name="history", description="Displays the history of speedtest results")
    async def history(self, ctx: commands.Context):
        """Displays the history of speedtest results"""
        if not self.speedtest_results:
            await ctx.send("No speedtest results available.")
            return

        embed = discord.Embed(
            title="Speedtest History",
            description="Here are the last 5 speedtest results:",
            color=discord.Color(0xfffffe)
        )

        for i, result in enumerate(self.speedtest_results[-5:], start=1):
            test_date = result.get('date', 'Unknown Date')
            embed.add_field(
                name=f"{test_date}",
                value=(
                    f"**Download:** {result['download']} Mbps\n"
                    f"**Upload:** {result['upload']} Mbps\n"
                    f"**Ping:** {result['ping']} ms"
                ),
                inline=False
            )

        await ctx.send(embed=embed)

    def _update_latency_history(self, ws_latency):
        self.latency_history.append(ws_latency)
        if len(self.latency_history) > 5:
            self.latency_history.pop(0)

    def _calculate_average_latency(self):
        return round(sum(self.latency_history) / len(self.latency_history), 2)

    def _create_initial_embed(self, avg_latency):
        embed = discord.Embed(
            title="Evaluating connection",
            description="Please wait while we gather the speedtest results.",
            color=discord.Color(0xfffffe)
        )
        embed.add_field(name="Latency information", value="", inline=False)
        embed.add_field(name="Network & transit", value=f"**{avg_latency}ms**", inline=True)
        return embed

    async def _perform_speedtest(self):
        return await asyncio.get_event_loop().run_in_executor(self.executor, self.run_speedtest)

    async def _create_final_embed(self, avg_latency, download_speed, upload_speed, ping):
        embed_color, embed_title, embed_description = self._determine_connection_status(avg_latency)
        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="Latency information", value="", inline=False)
        embed.add_field(name="Host", value=f"**{ping}ms**", inline=True)
        embed.add_field(name="Network and transit", value=f"**{avg_latency}ms**", inline=True)
        embed.add_field(name="Speedtest results", value="", inline=False)
        embed.add_field(name="Bot download", value=f"**{download_speed} Mbps**", inline=True)
        embed.add_field(name="Bot upload", value=f"**{upload_speed} Mbps**", inline=True)

        discord_status, last_updated = await self.check_discord_status()
        discord_status_field = self._create_discord_status_field(discord_status, last_updated)
        embed.add_field(**discord_status_field)

        return embed

    def _determine_connection_status(self, avg_latency):
        if avg_latency > 100:
            return (discord.Color(0xff4545), "Connection impacted", 
                    "Need better bot performance? Consider upgrading to a dedicated server for optimal performance. [Here's $100 on us to try out dedicated hosting with Linode](https://www.linode.com/lp/refer/?r=577180eb1019c3b67e5f5d732b5d66a2c5727fe9)")
        else:
            return (discord.Color(0x2bbd8e), "Connection OK", 
                    "Your connection is stable and performing well for bot operations.")

    async def check_discord_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discordstatus.com/api/v2/status.json") as response:
                if response.status == 200:
                    data = await response.json()
                    last_updated_str = data['page']['updated_at']
                    last_updated = int(datetime.datetime.fromisoformat(last_updated_str.replace('Z', '+00:00')).timestamp())
                    return data['status']['indicator'] != 'none', last_updated
                else:
                    return False, 0

    def _create_discord_status_field(self, discord_status, last_updated):
        status_message = ":warning: **Issues have been reported**" if discord_status else ":white_check_mark: **All services operational**"
        return {
            "name": "Discord status",
            "value": f"{status_message} as of **<t:{last_updated}:R>**",
            "inline": False
        }

    def run_speedtest(self):
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        download_speed = round(st.download() / 1_000_000, 2)
        upload_speed = round(st.upload() / 1_000_000, 2)
        ping = st.results.ping

        retries = 0
        max_retries = 3
        while ping > 250 and retries < max_retries:
            st.get_best_server()
            download_speed = round(st.download() / 1_000_000, 2)
            upload_speed = round(st.upload() / 1_000_000, 2)
            ping = st.results.ping
            retries += 1

        return download_speed, upload_speed, ping

    def _log_speedtest_result(self, download_speed, upload_speed, ping):
        """Log the speedtest result."""
        self.speedtest_results.append({
            "download": download_speed,
            "upload": upload_speed,
            "ping": ping,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        if len(self.speedtest_results) > 5:
            self.speedtest_results.pop(0)