import aiohttp
import asyncio
import discord
from redbot.core import commands

class VirusTotal(commands.Cog):
    """VirusTotal file upload and analysis via Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.suspicious_file_types = ['.exe', '.dll', '.scr', '.zip', '.rar', '.bat', '.cmd', '.js', '.jar', '.docm', '.xlsm', '.pptm']

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(name="virustotal", description="Submit a file for analysis via VirusTotal", aliases=["vt"])
    async def virustotal(self, ctx, file_url: str = None):
        async with ctx.typing():
            vt_key = await self.bot.get_shared_api_tokens("virustotal")
            if not vt_key.get("api_key"):
                await ctx.send(embed=self.create_error_embed('No VirusTotal API Key set', "Your Red instance doesn't have an API key set for VirusTotal.\n\nUntil you add an API key using `[p]set api`, the VirusTotal API will refuse your requests and this cog won't work."))
                return

            async with aiohttp.ClientSession() as session:
                try:
                    if file_url:
                        await self.analyze_url(ctx, session, file_url, vt_key["api_key"])
                    elif ctx.message.attachments:
                        await self.analyze_attachment(ctx, session, ctx.message.attachments[0], vt_key["api_key"])
                    else:
                        await ctx.send(embed=self.create_error_embed('No file provided', "The bot was unable to find content to submit for analysis!\nPlease provide one of the following when using this command:\n- URL file can be downloaded from\n- Drag-and-drop a file less than 25mb in size"))
                except (aiohttp.ClientResponseError, ValueError) as e:
                    await ctx.send(embed=self.create_error_embed('Failed to submit file', str(e)))
                except asyncio.TimeoutError:
                    await ctx.send(embed=self.create_error_embed('Request Timeout', "The bot was unable to complete the request due to a timeout."))
                except Exception as e:
                    await ctx.send(embed=self.create_error_embed('Unexpected Error', f"An unexpected error occurred: {str(e)}"))

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if not message.attachments:
            return

        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in self.suspicious_file_types):
                async with aiohttp.ClientSession() as session:
                    vt_key = await self.bot.get_shared_api_tokens("virustotal")
                    if vt_key.get("api_key"):
                        try:
                            await self.analyze_attachment(message.channel, session, attachment, vt_key["api_key"])
                        except Exception as e:
                            await message.channel.send(embed=self.create_error_embed('Failed to analyze attachment', str(e)))

    async def analyze_url(self, ctx, session, file_url, api_key):
        try:
            async with session.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": api_key}, data={"url": file_url}) as response:
                await self.handle_response(response, ctx, 'URL')
        except aiohttp.ClientError as e:
            await ctx.send(embed=self.create_error_embed('Client Error', f"An error occurred while analyzing the URL: {str(e)}"))

    async def analyze_attachment(self, ctx, session, attachment, api_key):
        try:
            async with session.get(attachment.url) as response:
                await self.handle_response(response, ctx, 'File')
        except aiohttp.ClientError as e:
            await ctx.send(embed=self.create_error_embed('Client Error', f"An error occurred while downloading the attachment: {str(e)}"))

    async def handle_response(self, response, ctx, analysis_type):
        if response.status != 200:
            raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
        try:
            data = await response.json()
        except aiohttp.ContentTypeError:
            raise ValueError(f"Invalid response received from {analysis_type} analysis: not a JSON response.")
        analysis_id = data.get("data", {}).get("id")
        if analysis_id:
            await self.check_results(ctx, analysis_id, ctx.author.id)
        else:
            raise ValueError(f"No analysis ID found in the {analysis_type} response.")

    async def check_results(self, ctx, analysis_id, user_id):
        # Check the analysis results periodically until the analysis is complete
        async with aiohttp.ClientSession() as session:
            headers = {"x-apikey": await self.bot.get_shared_api_tokens("virustotal").get("api_key")}
            url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            while True:
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=f"HTTP error {response.status}", headers=response.headers)
                        result_data = await response.json()
                        status = result_data.get("data", {}).get("attributes", {}).get("status")
                        if status == "completed":
                            break
                        await asyncio.sleep(5)  # Wait for 5 seconds before checking again
                except aiohttp.ClientError as e:
                    await ctx.send(embed=self.create_error_embed('Client Error', f"An error occurred while checking the analysis results: {str(e)}"))
                    return

            # Once the analysis is complete, send the results to the user
            analysis_results = result_data.get("data", {}).get("attributes", {}).get("results", {})
            embed = self.create_results_embed(analysis_results)
            user = self.bot.get_user(user_id)
            if user:
                try:
                    await user.send(embed=embed)
                except discord.HTTPException as e:
                    await ctx.send(embed=self.create_error_embed('Send Error', f"Failed to send results to the user: {str(e)}"))
            else:
                await ctx.send(embed=self.create_error_embed('User not found', "The bot was unable to send the results to the user."))

    def create_results_embed(self, results):
        # Create an embed with the analysis results
        embed = discord.Embed(title='VirusTotal Analysis Results', colour=discord.Colour.green())
        embed.add_field(name='Harmless', value=results.get('harmless', 0), inline=True)
        embed.add_field(name='Malicious', value=results.get('malicious', 0), inline=True)
        embed.add_field(name='Suspicious', value=results.get('suspicious', 0), inline=True)
        embed.add_field(name='Undetected', value=results.get('undetected', 0), inline=True)
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/check-circle-outline.png")
        return embed

    def create_error_embed(self, title, description):
        embed = discord.Embed(title=f'Error: {title}', description=description, colour=discord.Colour.red())
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle-outline.png")
        return embed



