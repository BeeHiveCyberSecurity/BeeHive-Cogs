import discord
import datetime
import time
import urllib.parse
import aiohttp
from redbot.core import Config, commands
from discord.ui import Button, View
from enum import Enum
from random import randint, choice
from typing import Final
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.menus import menu
from redbot.core.utils.chat_formatting import (
    bold,
    escape,
    italics,
    humanize_number,
    humanize_timedelta,
)

_ = T_ = Translator("ServerInfoCog", __file__)

class ServerInfoCog(commands.Cog):
    """See info about the servers your bot is in.
    
    For bot owners only.
    """

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=989839829839293)
        self.bot = bot

    # This cog does not store any End User Data
    async def red_get_data_for_user(self, *, user_id: int):
        return {}
    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        pass

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def serverinfo(self, ctx, details: bool = False):
        """
        Show server information.

        `details`: Shows more information when set to `True`.
        Default to False.
        """
        guild = ctx.guild
        created_at = _("Created on {date_and_time}. That's {relative_time}!").format(
            date_and_time=discord.utils.format_dt(guild.created_at),
            relative_time=discord.utils.format_dt(guild.created_at, "R"),
        )
        online = humanize_number(
            len([m.status for m in guild.members if m.status != discord.Status.offline])
        )
        total_users = guild.member_count and humanize_number(guild.member_count)
        text_channels = humanize_number(len(guild.text_channels))
        voice_channels = humanize_number(len(guild.voice_channels))
        stage_channels = humanize_number(len(guild.stage_channels))

        def _size(num: int):
            for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
                if abs(num) < 1024.0:
                    return "{0:.1f}{1}".format(num, unit)
                num /= 1024.0
            return "{0:.1f}{1}".format(num, "YB")

        def _bitsize(num: int):
            for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
                if abs(num) < 1000.0:
                    return "{0:.1f}{1}".format(num, unit)
                num /= 1000.0
            return "{0:.1f}{1}".format(num, "YB")

        shard_info = (
            _("\nShard ID: **{shard_id}/{shard_count}**").format(
                shard_id=humanize_number(guild.shard_id + 1),
                shard_count=humanize_number(ctx.bot.shard_count),
            )
            if ctx.bot.shard_count > 1
            else ""
        )
        # Logic from: https://github.com/TrustyJAID/Trusty-cogs/blob/master/serverstats/serverstats.py#L159
        online_stats = {
            _("Humans: "): lambda x: not x.bot,
            _(" • Bots: "): lambda x: x.bot,
            "\N{LARGE GREEN CIRCLE}": lambda x: x.status is discord.Status.online,
            "\N{LARGE ORANGE CIRCLE}": lambda x: x.status is discord.Status.idle,
            "\N{LARGE RED CIRCLE}": lambda x: x.status is discord.Status.do_not_disturb,
            "\N{MEDIUM WHITE CIRCLE}\N{VARIATION SELECTOR-16}": lambda x: (
                x.status is discord.Status.offline
            ),
            "\N{LARGE PURPLE CIRCLE}": lambda x: any(
                a.type is discord.ActivityType.streaming for a in x.activities
            ),
            "\N{MOBILE PHONE}": lambda x: x.is_on_mobile(),
        }
        member_msg = _("Users online: **{online}/{total_users}**\n").format(
            online=online, total_users=total_users
        )
        count = 1
        for emoji, value in online_stats.items():
            try:
                num = len([m for m in guild.members if value(m)])
            except Exception as error:
                print(error)
                continue
            else:
                member_msg += f"{emoji} {bold(humanize_number(num))} " + (
                    "\n" if count % 2 == 0 else ""
                )
            count += 1

        verif = {
            "none": _("0 - None"),
            "low": _("1 - Low"),
            "medium": _("2 - Medium"),
            "high": _("3 - High"),
            "highest": _("4 - Highest"),
        }

        joined_on = _(
            "{bot_name} joined this server on {bot_join}. That's over {since_join} days ago!"
        ).format(
            bot_name=ctx.bot.user.display_name,
            bot_join=guild.me.joined_at.strftime("%d %b %Y %H:%M:%S"),
            since_join=humanize_number((ctx.message.created_at - guild.me.joined_at).days),
        )

        pages = []

        page1 = discord.Embed(
            description=(f"{guild.description}\n\n" if guild.description else "") + created_at,
            colour=await ctx.embed_colour(),
        )
        page1.set_author(
            name=guild.name,
            icon_url="https://cdn.discordapp.com/emojis/457879292152381443.png"
            if "VERIFIED" in guild.features
            else "https://cdn.discordapp.com/emojis/508929941610430464.png"
            if "PARTNERED" in guild.features
            else None,
        )
        if guild.icon:
            page1.set_thumbnail(url=guild.icon)
        page1.add_field(name=_("Members:"), value=member_msg)
        pages.append(page1)

        page2 = discord.Embed(
            colour=await ctx.embed_colour(),
        )
        page2.add_field(
            name=_("Channels:"),
            value=_(
                "\N{SPEECH BALLOON} Text: {text}\n"
                "\N{SPEAKER WITH THREE SOUND WAVES} Voice: {voice}\n"
                "\N{STUDIO MICROPHONE} Stage: {stage}"
            ).format(
                text=bold(text_channels),
                voice=bold(voice_channels),
                stage=bold(stage_channels),
            ),
        )
        page2.add_field(
            name=_("Utility:"),
            value=_(
                "Owner: {owner}\nVerif. level: {verif}\nServer ID: {id}{shard_info}"
            ).format(
                owner=bold(str(guild.owner)),
                verif=bold(verif[str(guild.verification_level)]),
                id=bold(str(guild.id)),
                shard_info=shard_info,
            ),
            inline=False,
        )
        pages.append(page2)

        page3 = discord.Embed(
            colour=await ctx.embed_colour(),
        )
        page3.add_field(
            name=_("Misc:"),
            value=_(
                "AFK channel: {afk_chan}\nAFK timeout: {afk_timeout}\nCustom emojis: {emoji_count}\nRoles: {role_count}"
            ).format(
                afk_chan=bold(str(guild.afk_channel))
                if guild.afk_channel
                else bold(_("Not set")),
                afk_timeout=bold(humanize_timedelta(seconds=guild.afk_timeout)),
                emoji_count=bold(humanize_number(len(guild.emojis))),
                role_count=bold(humanize_number(len(guild.roles))),
            ),
            inline=False,
        )
        pages.append(page3)

        excluded_features = {
            # available to everyone since forum channels private beta
            "THREE_DAY_THREAD_ARCHIVE",
            "SEVEN_DAY_THREAD_ARCHIVE",
            # rolled out to everyone already
            "NEW_THREAD_PERMISSIONS",
            "TEXT_IN_VOICE_ENABLED",
            "THREADS_ENABLED",
            # available to everyone sometime after forum channel release
            "PRIVATE_THREADS",
        }
        custom_feature_names = {
            "VANITY_URL": "Vanity URL",
            "VIP_REGIONS": "VIP regions",
        }
        features = sorted(guild.features)
        if "COMMUNITY" in features:
            features.remove("NEWS")
        feature_names = [
            custom_feature_names.get(feature, " ".join(feature.split("_")).capitalize())
            for feature in features
            if feature not in excluded_features
        ]
        if guild.features:
            page4 = discord.Embed(
                colour=await ctx.embed_colour(),
            )
            page4.add_field(
                name=_("Server features:"),
                value="\n".join(
                    f"\N{WHITE HEAVY CHECK MARK} {feature}" for feature in feature_names
                ),
            )
            pages.append(page4)

        if guild.premium_tier != 0:
            page5 = discord.Embed(
                colour=await ctx.embed_colour(),
            )
            nitro_boost = _(
                "Tier {boostlevel} with {nitroboosters} boosts\n"
                "File size limit: {filelimit}\n"
                "Emoji limit: {emojis_limit}\n"
                "VCs max bitrate: {bitrate}"
            ).format(
                boostlevel=bold(str(guild.premium_tier)),
                nitroboosters=bold(humanize_number(guild.premium_subscription_count)),
                filelimit=bold(_size(guild.filesize_limit)),
                emojis_limit=bold(str(guild.emoji_limit)),
                bitrate=bold(_bitsize(guild.bitrate_limit)),
            )
            page5.add_field(name=_("Nitro Boost:"), value=nitro_boost)
            pages.append(page5)

        if guild.splash:
            page6 = discord.Embed(
                colour=await ctx.embed_colour(),
            )
            page6.set_image(url=guild.splash.replace(format="png"))
            pages.append(page6)

        for page in pages:
            page.set_footer(text=joined_on)

        # Create a View with interaction buttons for navigation
        class NavigationView(View):
            def __init__(self):
                super().__init__()
                self.add_item(Button(style=discord.ButtonStyle.secondary, label="Previous", custom_id="previous"))
                self.add_item(Button(style=discord.ButtonStyle.secondary, label="Next", custom_id="next"))

            @discord.ui.button(label='Previous', style=discord.ButtonStyle.secondary)
            async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                pass

            @discord.ui.button(label='Next', style=discord.ButtonStyle.secondary)
            async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                pass

        view = NavigationView()
        await ctx.send(embed=pages[0], view=view)
