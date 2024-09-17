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
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        return

    @commands.group()
    async def triage(self, ctx: Context):
        """
        Tria.ge is a cybersecurity platform that leverages artificial intelligence to automate and enhance the process of triaging security alerts by analyzing and prioritizing threats based on their potential impact and relevance.

        Learn more at https://tria.ge
        """
        pass

    @triage.command()
    async def setkey(self, ctx: Context, api_key: str):
        """Set the API key for tria.ge."""
        await self.bot.set_shared_api_tokens("triage", api_key=api_key)
        tokens = await self.bot.get_shared_api_tokens("triage")
        saved_key = tokens.get("api_key")
        if saved_key == api_key:
            await ctx.message.delete()
        else:
            embed = discord.Embed(title="Error", description="Failed to set API key. Please try again.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @triage.command()
    async def submit(self, ctx: Context, interactive: bool = False, password: str = None, timeout: int = None, network: str = "internet"):
        """Submit a file for analysis to the tria.ge API."""
        tokens = await self.bot.get_shared_api_tokens("triage")
        api_key = tokens.get("api_key")
        if not api_key:
            embed = discord.Embed(title="Error", description="API key not set. Use `[p]triage setkey` to set it.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if not ctx.message.attachments:
            embed = discord.Embed(title="Error", description="No file attached. Please upload a file to submit.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        data = {
            "kind": "file",
            "interactive": interactive,
            "defaults": {
                "timeout": timeout if timeout else 3600,
                "network": network
            }
        }

        attachment = ctx.message.attachments[0]
        try:
            file_data = await attachment.read()
            data["file"] = file_data
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred while reading the file: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if password:
            data["password"] = password

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with self.session.post("https://api.tria.ge/v0/samples", headers=headers, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    analysis_id = result['id']
                    embed = discord.Embed(title="Submission Successful", description=f"Submitted successfully. Analysis ID: {analysis_id}", color=discord.Color.green())
                    await ctx.send(embed=embed)
                    
                    # Polling for analysis results
                    embed = discord.Embed(title="Analysis", description="Waiting for analysis to complete...", color=discord.Color.blue())
                    await ctx.send(embed=embed)
                    while True:
                        async with self.session.get(f"https://api.tria.ge/v0/samples/{analysis_id}", headers=headers) as status_response:
                            if status_response.status == 200:
                                status_result = await status_response.json()
                                if status_result['status'] == 'reported':
                                    embed = discord.Embed(title="Analysis Completed", description=f"Analysis completed. Report URL: {status_result['report_url']}", color=discord.Color.green())
                                    await ctx.send(embed=embed)
                                    break
                                elif status_result['status'] == 'failed':
                                    embed = discord.Embed(title="Analysis Failed", description="Analysis failed.", color=discord.Color.red())
                                    await ctx.send(embed=embed)
                                    break
                            else:
                                embed = discord.Embed(title="Error", description=f"Failed to get analysis status. Status code: {status_response.status}", color=discord.Color.red())
                                await ctx.send(embed=embed)
                                break
                            await asyncio.sleep(10)  # Wait for 10 seconds before polling again
                else:
                    embed = discord.Embed(title="Error", description=f"Failed to submit. Status code: {response.status}", color=discord.Color.red())
                    await ctx.send(embed=embed)
        except aiohttp.ClientError as e:
            embed = discord.Embed(title="Error", description=f"An error occurred while submitting: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)
