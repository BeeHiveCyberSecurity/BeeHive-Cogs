import discord  # type: ignore
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

    @commands.hybrid_command(name="ping", description="Displays the bot's latency, download speed, and upload speed")
    async def ping(self, ctx: commands.Context):
        """Displays the bot's latency, download speed, and upload speed"""
        await ctx.defer()
        ws_latency = round(self.bot.latency * 1000, 2)

        self.latency_history.append(ws_latency)
        if len(self.latency_history) > 5:
            self.latency_history.pop(0)
        avg_latency = round(sum(self.latency_history) / len(self.latency_history), 2)

        # Pre-fill variables for embed
        embed_color = discord.Color(0xfffffe)
        embed_title = "Evaluating connection"
        embed_description = "Please wait while we gather the speedtest results."

        # Check for Discord status
        discord_status, discord_description, last_updated = await self.check_discord_status()

        # Send initial response with latency information
        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="Latency information", value="", inline=False)
        embed.add_field(name="Network & transit", value=f"**{avg_latency}ms**", inline=True)
        initial_message = await ctx.send(embed=embed)

        # Run speedtest in the background
        try:
            download_speed, upload_speed, ping = await asyncio.get_event_loop().run_in_executor(self.executor, self.run_speedtest)
        except Exception as e:
            await initial_message.edit(content=f"An error occurred while performing the speed test: {e}", embed=None)
            return

        if ping > 250:  # If still high after retries
            await initial_message.edit(content="Network conditions are currently fluctuating too much to measure conditions accurately. Please try again later.", embed=None)
            return

        if avg_latency > 100:  # Adjust thresholds as needed
            embed_color = discord.Color(0xff4545)
            embed_title = "Connection impacted"
            embed_description = "Need better bot performance? Consider upgrading to a dedicated server for optimal performance. [Here's $100 on us to try out dedicated hosting with Linode](https://www.linode.com/lp/refer/?r=577180eb1019c3b67e5f5d732b5d66a2c5727fe9)"
        else:
            embed_color = discord.Color(0x2bbd8e)
            embed_title = "Connection OK"
            embed_description = "Your connection is stable and performing well for bot operations."

        # Update the embed with speedtest results
        embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        embed.add_field(name="Latency information", value="", inline=False)
        embed.add_field(name="Host", value=f"**{ping}ms**", inline=True)
        embed.add_field(name="Network/Transit", value=f"**{avg_latency}ms**", inline=True)
        embed.add_field(name="Speedtest results", value="", inline=False)
        embed.add_field(name="Bot download", value=f"**{download_speed} Mbps**", inline=True)
        embed.add_field(name="Bot upload", value=f"**{upload_speed} Mbps**", inline=True)
        
        # Add Discord status to the final embed
        if discord_status:
            embed.add_field(name="Discord status", value=f":warning: **Issues have been reported**: {discord_description}\nLast updated: <t:{last_updated}:R>", inline=False)
        else:
            embed.add_field(name="Discord status", value=f":white_check_mark: **No outages reported**\nLast updated: <t:{last_updated}:R>", inline=False)

        await initial_message.edit(embed=embed)

    async def check_discord_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discordstatus.com/api/v2/status.json") as response:
                if response.status == 200:
                    data = await response.json()
                    last_updated_str = data['page']['updated_at']
                    last_updated = int(datetime.datetime.fromisoformat(last_updated_str.replace('Z', '+00:00')).timestamp())
                    return data['status']['indicator'] != 'none', data['status']['description'], last_updated
                else:
                    return False, "Unable to fetch Discord status", 0

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