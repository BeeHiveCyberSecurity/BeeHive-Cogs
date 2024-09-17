import discord  # type: ignore
import asyncio  # type: ignore
from discord.ext import commands  # type: ignore
from redbot.core import Config, commands  # type: ignore
from redbot.core.bot import Red  # type: ignore
from redbot.core.commands import Context  # type: ignore
import io
import triage
from triage import Client as TriageClient  # Import the Client class from the triage module and alias it

class Triage(commands.Cog):
    """
    Submit files for analysis to the tria.ge API.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.triage_client = None

    def cog_unload(self):
        if self.triage_client:
            self.triage_client.close()

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

        attachment = ctx.message.attachments[0]
        try:
            file_data = await attachment.read()
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred while reading the file: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if not self.triage_client:
            self.triage_client = TriageClient(api_key, root_url="https://api.tria.ge")

        try:
            file_stream = io.BytesIO(file_data)
            submission = await self.triage_client.submit_sample_file(attachment.filename, file_stream)
            analysis_id = submission['id']
            embed = discord.Embed(title="Submission Successful", description=f"Submitted successfully. Analysis ID: {analysis_id}", color=discord.Color.green())
            await ctx.send(embed=embed)
            
            # Polling for analysis results
            embed = discord.Embed(title="Analysis", description="Waiting for analysis to complete...", color=discord.Color.blue())
            await ctx.send(embed=embed)
            while True:
                status_result = await self.triage_client.get_sample_status(analysis_id)
                if status_result['status'] == 'reported':
                    embed = discord.Embed(title="Analysis Completed", description=f"Analysis completed. Report URL: {status_result['report_url']}", color=discord.Color.green())
                    await ctx.send(embed=embed)
                    
                    # Fetching file overview
                    overview_result = await self.triage_client.get_sample_overview(analysis_id)
                    
                    # Extracting fields from OverviewAnalysis
                    score = overview_result.get('score', 'N/A')
                    family = ', '.join(overview_result.get('family', []))
                    tags = ', '.join(overview_result.get('tags', []))
                    
                    # Extracting fields from OverviewTarget
                    tasks = ', '.join(overview_result.get('tasks', []))
                    target_tags = ', '.join(overview_result.get('target_tags', []))  # Corrected key
                    target_family = ', '.join(overview_result.get('target_family', []))  # Corrected key
                    signatures = ', '.join([sig['name'] for sig in overview_result.get('signatures', [])])
                    iocs = overview_result.get('iocs', 'N/A')
                    
                    embed = discord.Embed(title="File Overview", color=discord.Color.blue())
                    embed.add_field(name="Score", value=score, inline=False)
                    embed.add_field(name="Family", value=family, inline=False)
                    embed.add_field(name="Tags", value=tags, inline=False)
                    embed.add_field(name="Tasks", value=tasks, inline=False)
                    embed.add_field(name="Target Tags", value=target_tags, inline=False)
                    embed.add_field(name="Target Family", value=target_family, inline=False)
                    embed.add_field(name="Signatures", value=signatures, inline=False)
                    embed.add_field(name="IOCs", value=iocs, inline=False)
                    
                    await ctx.send(embed=embed)
                    break
                elif status_result['status'] == 'failed':
                    embed = discord.Embed(title="Analysis Failed", description="Analysis failed.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    break
                await asyncio.sleep(10)  # Wait for 10 seconds before polling again
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred while submitting: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)
