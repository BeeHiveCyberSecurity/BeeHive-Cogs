import aiohttp  # type: ignore
import discord  # type: ignore
import asyncio  # type: ignore
from discord.ext import commands  # type: ignore
from redbot.core import Config, commands  # type: ignore
from redbot.core.bot import Red  # type: ignore
from redbot.core.commands import Context  # type: ignore

class Triage(commands.Cog):
    """
    Submit files for analysis to the tria.ge API.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(api_key=None)
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        return

    @commands.group()
    async def triage(self, ctx: Context):
        """Commands for interacting with the tria.ge API."""
        pass

    @triage.command()
    async def set_api_key(self, ctx: Context, api_key: str):
        """Set the API key for tria.ge."""
        await self.config.api_key.set(api_key)
        await ctx.send("API key set successfully.")

    @triage.command()
    async def submit_file(self, ctx: Context, file_url: str):
        """Submit a file for analysis to the tria.ge API."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("API key not set. Use `[p]triage set_api_key` to set it.")
            return

        try:
            async with self.session.get(file_url) as response:
                if response.status != 200:
                    await ctx.send("Failed to download the file.")
                    return
                file_data = await response.read()
        except aiohttp.ClientError as e:
            await ctx.send(f"An error occurred while downloading the file: {e}")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/octet-stream"
        }
        try:
            async with self.session.post("https://api.tria.ge/v0/samples", headers=headers, data=file_data) as response:
                if response.status == 201:
                    result = await response.json()
                    analysis_id = result['id']
                    await ctx.send(f"File submitted successfully. Analysis ID: {analysis_id}")
                    
                    # Polling for analysis results
                    await ctx.send("Waiting for analysis to complete...")
                    while True:
                        async with self.session.get(f"https://api.tria.ge/v0/samples/{analysis_id}", headers=headers) as status_response:
                            if status_response.status == 200:
                                status_result = await status_response.json()
                                if status_result['status'] == 'reported':
                                    await ctx.send(f"Analysis completed. Report URL: {status_result['report_url']}")
                                    break
                                elif status_result['status'] == 'failed':
                                    await ctx.send("Analysis failed.")
                                    break
                            await asyncio.sleep(10)  # Wait for 10 seconds before polling again
                else:
                    await ctx.send(f"Failed to submit file. Status code: {response.status}")
        except aiohttp.ClientError as e:
            await ctx.send(f"An error occurred while submitting the file: {e}")
