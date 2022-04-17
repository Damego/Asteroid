import os
from datetime import datetime
from re import compile
from typing import List, Union

from discord import Attachment, Embed, Guild, Member, PublicUserFlags, Role, TextChannel
from discord_slash import (
    Button,
    ButtonStyle,
    ContextMenuType,
    MenuContext,
    SlashCommandOptionType,
    SlashContext,
)
from discord_slash.cog_ext import cog_context_menu as context_menu
from discord_slash.cog_ext import cog_slash as slash_command
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option

from utils import (
    AsteroidBot,
    Cog,
    CogDisabledOnGuild,
    DiscordColors,
    SystemChannels,
    _cog_is_enabled,
    bot_owner_or_permissions,
    get_content,
    is_enabled,
    paginator,
    transform_permission,
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
        self.project_lines_count = 0
        #self.__get_lines_count()  # Ubuntu and Windows has different output format.
        # TODO: Make support for Ubuntu

    def __get_lines_count(self):
        os.system("pygount --format=summary --suffix=py --out=lines_count.txt")
        with open("lines_count.txt") as f:
            lines = f.readlines()
        self.project_lines_count = int(lines[-1].split()[-2])

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

        channel = self.bot.get_channel(SystemChannels.SERVERS_UPDATE_CHANNEL)
        await channel.send(embed=embed)

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

        channel = self.bot.get_channel(SystemChannels.SERVERS_UPDATE_CHANNEL)
        await channel.send(embed=embed)

    @Cog.listener()
    async def on_slash_command(self, ctx: SlashContext):
        if self.slash_use_channel is None:
            self.slash_use_channel = self.bot.get_channel(SystemChannels.COMMANDS_USING_CHANNEL)

        embed = Embed(
            title=self.bot.get_transformed_command_name(ctx),
            color=DiscordColors.EMBED_COLOR,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(
            text=f"{ctx.author.name} | {ctx.author_id}", icon_url=ctx.author.avatar_url
        )
        if ctx.kwargs:
            options = "\n".join([f"{option}: {value}" for option, value in ctx.kwargs.items()])
            embed.add_field(name="Options", value=options)
        if ctx.guild:
            embed.add_field(
                name="Guild Information",
                value=f"Name: {ctx.guild.name}\nID: {ctx.guild_id}",
            )

        await self.slash_use_channel.send(embed=embed)

    @slash_subcommand(base="info", name="user", description="Shows information about guild member")
    @is_enabled()
    async def get_member_information_slash(self, ctx: SlashContext, member: Member = None):
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
        member_status = status.get(str(member.status))

        member_roles = [role.mention for role in member.roles if role.name != "@everyone"][::-1]
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
                levels_enabled = await _cog_is_enabled(self.bot.get_cog("Levels"), ctx.guild_id)
            except CogDisabledOnGuild:
                levels_enabled = False

        if levels_enabled:
            await self._get_levels_info(ctx, member.id, embed, content)

        return embed

    async def _get_levels_info(self, ctx: SlashContext, user_id: int, embed: Embed, content: dict):
        content = content["LEVELING"]
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(user_id)
        user_level = user_data.level
        xp_to_next_level = formula_of_experience(user_level)

        user_level_text = content["CURRENT_LEVEL_TEXT"].format(level=user_level)
        user_exp_text = content["CURRENT_EXP_TEXT"].format(
            exp=user_data.xp, exp_to_next_level=xp_to_next_level, exp_amount=user_data.xp_amount
        )
        user_voice_time_count = content["TOTAL_VOICE_TIME"].format(
            voice_time=self._format_voice_time(user_data.voice_time_count, content)
        )

        embed.add_field(
            name=content["LEVELING_INFO_TITLE_TEXT"],
            value=f"{user_level_text}\n{user_exp_text}\n{user_voice_time_count}",
        )

    def _format_voice_time(self, voice_time: int, content: dict):
        days = (voice_time // 60) // 24
        hours = (voice_time // 60) % 24
        minutes = voice_time % 60
        formatted = ""
        if days != 0:
            formatted += f" {days} {content['DAYS']}"
        if hours != 0:
            formatted += f" {hours:02} {content['HOURS']}"
        if minutes != 0:
            formatted += f" {minutes:02} {content['MINUTES']}"
        return formatted.strip() if formatted else "-"

    @slash_subcommand(base="info", name="bot", description="Show information of bot")
    @is_enabled()
    async def bot_info(self, ctx: SlashContext):
        await ctx.defer()
        content = get_content(
            "BOT_INFO_COMMAND", lang=await self.bot.get_guild_bot_lang(ctx.guild_id)
        )
        embed = Embed(title=content["BOT_INFORMATION_TITLE"], color=DiscordColors.EMBED_COLOR)

        if commits := self._format_commits():
            embed.description = f"{content['GITHUB_UPDATES']}\n{commits}"
        users_count = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(
            name=content["GENERAL_INFORMATION"],
            value=f"{content['CREATED_AT']} <t:{int(self.bot.user.created_at.timestamp())}:F>\n"
            f"{content['SERVERS_COUNT']} `{len(self.bot.guilds)}`\n"
            f"{content['USERS_COUNT']} `{users_count}`",
        )
        embed.add_field(
            name=content["TECHNICAL_INFORMATION"],
            value=f"{content['BOT_VERSION']} `v2`\n"
            f"{content['LINES_OF_CODE']} `{self.project_lines_count}`\n"
            f"{content['LIBRARIES']}\n"
            "・ `discord.py v1.7.3`\n"
            "・ custom `discord-py-interactions v3`\n",
        )

        await ctx.send(embed=embed)

    def _format_commits(self):
        commits = self.bot.github_repo_commits
        return "".join(
            f"[`{commit.sha[:7]}`]({commit.commit.html_url[:-33]}) **{commit.commit.message.splitlines()[0]}**\n"
            for commit in commits
        )

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
    @is_enabled()
    async def check_bots(self, ctx: SlashContext):
        bots_list = [member for member in ctx.guild.members if member.bot]

        content = f"**Offline bots in {ctx.guild.name} server**\n"
        content += ", ".join(f"{bot.mention}" for bot in bots_list if str(bot.status) == "offline")

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

    @slash_subcommand(base="server", name="roles", description="Show's all server roles")
    @is_enabled()
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

    @slash_subcommand(base="misc", name="send_image", description="Send image in embed from link")
    @is_enabled()
    async def send_image(self, ctx: SlashContext, url: str):
        if not url_rx.match(url):
            return await ctx.send("Not link", hidden=True)

        embed = Embed(title="Image", color=await self.bot.get_embed_color(ctx.guild_id))
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="misc",
        name="attachment",
        description="Sends file",
        options=[
            create_option(
                name="attachment",
                description="Send attachment",
                option_type=SlashCommandOptionType.ATTACHMENT,
                required=True,
            ),
        ],
    )
    async def test_attachment(self, ctx: SlashContext, attachment: Attachment):
        file = await attachment.to_file()
        await ctx.send(file=file)

    @slash_subcommand(base="server", name="bot_nick", description="Set nick to bot on your server")
    @is_enabled()
    @bot_owner_or_permissions(manage_nicknames=True)
    async def server_set_bot_nick(self, ctx: SlashContext, nick: str):
        if ctx.guild is None:
            return await ctx.send("Availble only in guild!")
        await ctx.me.edit(nick=nick)
        await ctx.send("Done", hidden=True)


def setup(bot):
    bot.add_cog(Misc(bot))
