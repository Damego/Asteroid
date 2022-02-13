from datetime import datetime
import os
from typing import Union, List
from re import compile

from aiohttp import ClientSession
from discord import (
    Member,
    Embed,
    Role,
    Guild,
    PublicUserFlags,
    Webhook,
    AsyncWebhookAdapter,
    TextChannel,
    Forbidden,
    ChannelType,
    File
)
from discord.ext import commands
from discord_slash import SlashContext, ContextMenuType, MenuContext, Button, ButtonStyle, SlashCommandOptionType
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu,
)
from discord_slash.utils.manage_commands import create_option

from my_utils import (
    AsteroidBot,
    get_content,
    Cog,
    CogDisabledOnGuild,
    is_enabled,
    _cog_is_enabled,
    transform_permission,
    paginator,
    consts,
)
from .levels._levels import formula_of_experience


url_rx = compile(r"https?://(?:www\.)?.+")


class Misc(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = "💡"
        self.name = "Misc"

        self.slash_use_channel: TextChannel = None

    async def send_guilds_update_webhooks(self, embed: Embed):
        async with ClientSession() as session:
            webhook = Webhook.from_url(
                os.getenv("WEBHOOK_GUILDS_UPDATE"), adapter=AsyncWebhookAdapter(session)
            )
            await webhook.send(embed=embed, username="Asteroid | Servers Information")

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        guild_info = (
            f"**Название:** {guild.name}\n"
            f"**ID:** {guild.id}\n"
            f"**Количество участников:** {guild.member_count}\n"
            f"**Создатель сервера:** {guild.owner.display_name}"
        )
        embed = Embed(title="Новый сервер!", description=guild_info, color=0x00FF00)
        embed.set_thumbnail(url=guild.icon_url)
        await self.send_guilds_update_webhooks(embed)

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        guild_info = (
            f"**Название:** {guild.name}\n"
            f"**ID:** {guild.id}\n"
            f"**Количество участников:** {guild.member_count}\n"
            f"**Создатель сервера:** {guild.owner.display_name}"
        )

        embed = Embed(title="Минус сервак!", description=guild_info, color=0xFF0000)
        embed.set_thumbnail(url=guild.icon_url)
        await self.send_guilds_update_webhooks(embed)

    @Cog.listener()
    async def on_slash_command(self, ctx: SlashContext):
        if self.slash_use_channel is None:
            self.slash_use_channel = self.bot.get_channel(933755239583080448)
        await self.slash_use_channel.send(
            f"{datetime.utcnow()} | **{ctx.guild.name}** | {ctx.guild_id} | **{ctx.author.display_name}**\n"
            f"`/{self.bot.get_transformed_command_name(ctx)} {ctx.kwargs}`"
        )

    @slash_command(name="info", description="Shows information about guild member")
    @is_enabled()
    async def get_member_information_slash(
        self, ctx: SlashContext, member: Member = None
    ):
        embed = await self._get_embed_member_info(ctx, member or ctx.author)
        await ctx.send(embed=embed)

    @context_menu(name="Profile", target=ContextMenuType.USER)
    @is_enabled()
    async def get_member_information_context(self, ctx: MenuContext):
        member = ctx.target_author
        embed = await self._get_embed_member_info(ctx, member)
        await ctx.send(embed=embed)

    async def _get_embed_member_info(
        self, ctx: Union[SlashContext, MenuContext], member: Member
    ) -> Embed:
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("FUNC_MEMBER_INFO", lang=lang)

        status = content["MEMBER_STATUS"]
        about_text = content["ABOUT_TITLE"].format(member.display_name)
        general_info_title_text = content["GENERAL_INFO_TITLE"]

        is_bot = "<:discord_bot_badge:924198977367318548>" if member.bot else ""
        user_badges = self._get_user_badges(member.public_flags)
        badges_text = (
            f"**{content['BADGES_TEXT']}** {user_badges}" if user_badges else ""
        )
        member_status = status.get(str(member.status))

        member_roles = [
            role.mention for role in member.roles if role.name != "@everyone"
        ][::-1]
        member_roles = ", ".join(member_roles)
        role_content = (
            f"**{content['TOP_ROLE_TEXT']}** {member.top_role.mention}"
            f"\n**{content['ROLES_TEXT']}** {member_roles}"
            if member_roles and len(member_roles) < 1024
            else ""
        )

        embed = Embed(title=about_text, color=await self.bot.get_embed_color(ctx.guild_id))
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar_url)
        embed.add_field(
            name=general_info_title_text,
            value=f"""
                **{content['FULL_NAME_TEXT']}** {member} {is_bot}
                {badges_text}
                **{content['DISCORD_REGISTRATION_TEXT']}** <t:{int(member.created_at.timestamp())}:F>
                **{content['JOINED_ON_SERVER_TEXT']}** <t:{int(member.joined_at.timestamp())}:F>
                **{content['CURRENT_STATUS_TEXT']}** {member_status}
                {role_content}
                """,
            inline=False,
        )

        if member.bot:
            levels_enabled = False
        else:
            try:
                levels_enabled = _cog_is_enabled(
                    self.bot.get_cog("Levels"), ctx.guild_id
                )
            except CogDisabledOnGuild:
                levels_enabled = False

        if levels_enabled:
            await self._get_levels_info(ctx, member.id, embed, content)

        return embed

    async def _get_levels_info(
        self, ctx: SlashContext, user_id: int, embed: Embed, content: dict
    ):
        content = content["LEVELING"]
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(user_id)

        user_level = user_data.level
        user_exp, user_exp_amount, user_voice_time = map(
            int,
            [user_data.xp, user_data.xp_amount, user_data.voice_time_count],
        )
        xp_to_next_level = formula_of_experience(user_level)

        user_level_text = content["CURRENT_LEVEL_TEXT"].format(level=user_level)
        user_exp_text = content["CURRENT_EXP_TEXT"].format(
            exp=user_exp, exp_to_next_level=xp_to_next_level, exp_amount=user_exp_amount
        )
        user_voice_time_count = content["TOTAL_VOICE_TIME"].format(
            voice_time=user_voice_time / 60
        )

        embed.add_field(
            name=content["LEVELING_INFO_TITLE_TEXT"],
            value=f"{user_level_text}\n{user_exp_text}\n{user_voice_time_count}",
        )

    @staticmethod
    def _get_user_badges(public_flags: PublicUserFlags) -> str:
        badges = ""
        if public_flags.staff:
            badges += "<:Discordstaff:904695373350707210> "
        if public_flags.partner:
            badges += "<:New_partner_badge:904695373363298304>"
        if public_flags.hypesquad:
            badges += "<:HypeSquad_Event_Badge:904695519270551612>"
        if public_flags.bug_hunter:
            badges += "<:Bug_hunter_badge:904695373300383744> "
        if public_flags.hypesquad_bravery:
            badges += "<:Hypesquad_bravery_badge:904695373606555648>"
        if public_flags.hypesquad_brilliance:
            badges += "<:Hypesquad_brilliance_badge:904695373321367582>"
        if public_flags.hypesquad_balance:
            badges += "<:Hypesquad_balance_badge:904695373367509002>"
        if public_flags.early_supporter:
            badges += "<:Early_supporter_badge:904695372931280947>"
        if public_flags.bug_hunter_level_2:
            badges += "<:Bug_buster_badge:904695373312950312>"
        if public_flags.early_verified_bot_developer:
            badges += "<:Verified_developer_badge:904695373401038848>"

        return badges

    @slash_subcommand(base="misc", name="ping", description="Show bot latency")
    @is_enabled()
    async def ping(self, ctx: SlashContext):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("FUNC_PING", lang=guild_data.configuration.language)

        embed = Embed(
            title="🏓 Pong!",
            description=content.format(int(self.bot.latency * 1000)),
            color=guild_data.configuration.embed_color,
        )

        await ctx.send(embed=embed)

    @slash_subcommand(
        base="server",
        name="offline_bots",
        description="Shows all offline bots in server",
    )
    async def check_bots(self, ctx: SlashContext):
        bots_list = [member for member in ctx.guild.members if member.bot]

        content = f"**Offline bots in {ctx.guild.name} server**\n"
        content += ", ".join(
            f"{bot.mention}" for bot in bots_list if str(bot.status) == "offline"
        )

        await ctx.send(content=content)

    @slash_subcommand(
        base="server",
        name="role_perms",
        description="Shows a role permissions in the server",
    )
    @is_enabled()
    async def guild_role_permissions(self, ctx: SlashContext, role: Role):
        description = "".join(
            f"✅ {transform_permission(permission[0])}\n"
            if permission[1]
            else f"❌ {transform_permission(permission[0])}\n"
            for permission in role.permissions
        )

        embed = Embed(
            title=f"Server permissions for {role.name} role",
            description=description,
            color=await self.bot.get_embed_color(ctx.guild_id),
        )

        await ctx.send(embed=embed)

    @slash_command(name="invite", description="Send's bot invite link")
    @is_enabled()
    async def invite_bot(self, ctx: SlashContext):
        content = get_content(
            "INVITE_COMMAND", lang=await self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        components = [
            [
                Button(
                    style=ButtonStyle.URL,
                    label=content["INVITE_BUTTON_NO_PERMS"],
                    url=self.bot.no_perms_invite_link,
                ),
                Button(
                    style=ButtonStyle.URL,
                    label=content["INVITE_BUTTON_ADMIN"],
                    url=self.bot.admin_invite_link,
                ),
                Button(
                    style=ButtonStyle.URL,
                    label=content["INVITE_BUTTON_RECOMMENDED"],
                    url=self.bot.recommended_invite_link,
                ),
            ]
        ]

        await ctx.send(
            content["CLICK_TO_INVITE_TEXT"].format(link=self.bot.no_perms_invite_link),
            components=components,
        )

    @slash_subcommand(
        base="server", name="roles", description="Show's all server roles"
    )
    async def send_server_roles(self, ctx: SlashContext):
        guild_roles: List[Role] = ctx.guild.roles[::-1]
        embeds: List[Embed] = []

        for count, role in enumerate(guild_roles, start=1):
            if count == 1:
                embed = Embed(title=f"Roles of {ctx.guild.name} server", description="")
            if count % 25 == 0:
                embeds.append(embed)
                embed = Embed(title=f"Roles of {ctx.guild.name} server", description="")
            embed.description += f"{count}. {role.mention} | {role.id} \n"
        if embed.description:
            embeds.append(embed)

        if len(embeds) > 1:
            _paginator = paginator.Paginator(
                self.bot, ctx, paginator.PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds
            )
            await _paginator.start()
        else:
            await ctx.send(embed=embeds[0])

    @slash_subcommand(
        base="misc", name="send_image", description="Send image in embed from link"
    )
    async def send_image(self, ctx: SlashContext, url: str):
        if not url_rx.match(url):
            return await ctx.send("Not link", hidden=True)

        embed = Embed()
        embed.set_image(url=url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
