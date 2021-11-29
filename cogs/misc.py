import os

import aiohttp
from discord import Member, Embed, Role, Guild, PublicUserFlags, Webhook, AsyncWebhookAdapter
from discord_components import Button, ButtonStyle
from discord_slash import SlashContext, ContextMenuType, MenuContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu
)

from my_utils import AsteroidBot, get_content, Cog, _is_enabled, CogDisabledOnGuild
from .levels._levels import formula_of_experience


class Misc(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '💡'
        self.name = 'Misc'

    async def send_guilds_update_webhooks(self, embed: Embed):
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(os.getenv('WEBHOOK_GUILDS_UPDATE'), adapter=AsyncWebhookAdapter(session))
            await webhook.send(embed=embed, username='Asteroid | Servers Information')

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        guild_info = f"**Название:** {guild.name}\n" \
                     f"**ID:** {guild.id}\n" \
                     f"**Количество участников:** {guild.member_count}\n" \
                     f"**Создатель сервера:** {guild.owner.display_name}"
        embed = Embed(
            title='Новый сервер!',
            description=guild_info,
            color=0x00ff00
        )
        embed.set_thumbnail(url=guild.icon_url)
        await self.send_guilds_update_webhooks(embed)

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        guild_info = f"**Название:** {guild.name}\n" \
                     f"**ID:** {guild.id}\n" \
                     f"**Количество участников:** {guild.member_count}\n" \
                     f"**Создатель сервера:** {guild.owner.display_name}"

        embed = Embed(
            title='Минус сервак!',
            description=guild_info,
            color=0xff0000
        )
        embed.set_thumbnail(url=guild.icon_url)
        await self.send_guilds_update_webhooks(embed)

    @slash_command(
        name='info',
        description='Out information about guild member'
    )
    async def get_member_information_slash(self, ctx: SlashContext, member: Member = None):
        if member is None:
            member = ctx.author
        embed = self._get_embed_member_info(ctx, member)
        await ctx.send(embed=embed)

    @context_menu(
        name='Get information',
        target=ContextMenuType.USER
    )
    async def get_member_information_context(self, ctx: MenuContext):
        member = ctx.target_author
        embed = self._get_embed_member_info(ctx, member)
        await ctx.send(embed=embed)

    def _get_embed_member_info(self, ctx: SlashContext, member: Member) -> Embed:
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_MEMBER_INFO', lang=lang)

        status = content['MEMBER_STATUS']
        about_text = content['ABOUT_TITLE'].format(member.display_name)
        general_info_title_text = content['GENERAL_INFO_TITLE']
        is_bot = '<:discord_bot_badge:904659785180401694>' if member.bot else ''
        user_badges = self._get_user_badges(member.public_flags)

        embed = Embed(title=about_text, color=self.bot.get_embed_color(ctx.guild_id))
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f'{ctx.author.name}', icon_url=ctx.author.avatar_url)

        member_roles = [role.mention for role in member.roles if role.name != "@everyone"][::-1]
        member_roles = ', '.join(member_roles)
        member_status = str(member.status)

        embed.add_field(
            name=general_info_title_text,
            value=f"""
                **{content['FULL_NAME_TEXT']}** {member} {is_bot}
                **{content['BADGES_TEXT']}** {user_badges}
    
                **{content['DISCORD_REGISTRATION_TEXT']}** <t:{int(member.created_at.timestamp())}:F>
                **{content['JOINED_ON_SERVER_TEXT']}** <t:{int(member.joined_at.timestamp())}:F>
                **{content['CURRENT_STATUS_TEXT']}** {status.get(member_status)}
                **{content['TOP_ROLE_TEXT']}** {member.top_role.mention}
                **{content['ROLES_TEXT']}** {member_roles}
                """,
            inline=False
        )

        if member.bot:
            levels_enabled = False
        else:
            try:
                levels_enabled = _is_enabled(self.bot.get_cog('Levels'), ctx.guild_id)
            except CogDisabledOnGuild:
                levels_enabled = False

        if levels_enabled:
            self._get_levels_info(ctx, member.id, embed, content)

        return embed

    def _get_levels_info(self, ctx: SlashContext, user_id: int, embed: Embed, content: dict):
        content = content['LEVELING']
        users_collection = self.bot.get_guild_users_collection(ctx.guild_id)
        user_data = users_collection.find_one({'_id': str(user_id)})

        if user_data is None:
            return
        user_stats = user_data.get('leveling')
        if user_stats is None:
            return

        user_level = user_stats['level']
        user_exp, user_exp_amount, user_voice_time = map(
            int,
            [
                user_stats['xp'],
                user_stats['xp_amount'],
                user_data['voice_time_count']
            ]
        )
        xp_to_next_level = formula_of_experience(user_level)

        user_level_text = content['CURRENT_LEVEL_TEXT'].format(
            level=user_level
        )
        user_exp_text = content['CURRENT_EXP_TEXT'].format(
            exp=user_exp,
            exp_to_next_level=xp_to_next_level,
            exp_amount=user_exp_amount
        )
        user_voice_time_count = content['TOTAL_VOICE_TIME'].format(
            voice_time=user_voice_time
        )

        embed.add_field(
            name=content['LEVELING_INFO_TITLE_TEXT'],
            value=f'{user_level_text}\n{user_exp_text}\n{user_voice_time_count}'
        )

    @staticmethod
    def _get_user_badges(public_flags: PublicUserFlags) -> str:
        badges = ''
        if public_flags.staff:
            badges += '<:Discordstaff:904695373350707210> '
        if public_flags.partner:
            badges += '<:New_partner_badge:904695373363298304>'
        if public_flags.hypesquad:
            badges += '<:HypeSquad_Event_Badge:904695519270551612>'
        if public_flags.bug_hunter:
            badges += '<:Bug_hunter_badge:904695373300383744> '
        if public_flags.hypesquad_bravery:
            badges += '<:Hypesquad_bravery_badge:904695373606555648>'
        if public_flags.hypesquad_brilliance:
            badges += '<:Hypesquad_brilliance_badge:904695373321367582>'
        if public_flags.hypesquad_balance:
            badges += '<:Hypesquad_balance_badge:904695373367509002>'
        if public_flags.early_supporter:
            badges += '<:Early_supporter_badge:904695372931280947>'
        if public_flags.bug_hunter_level_2:
            badges += '<:Bug_buster_badge:904695373312950312>'
        if public_flags.early_verified_bot_developer:
            badges += '<:Verified_developer_badge:904695373401038848>'

        return badges

    @slash_subcommand(
        base='misc',
        name='ping',
        description='Show bot latency'
    )
    async def ping(self, ctx: SlashContext):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_PING', lang=lang)

        embed = Embed(
            title='🏓 Pong!',
            description=content.format(int(self.bot.latency * 1000)),
            color=self.bot.get_embed_color(ctx.guild_id)
        )

        await ctx.send(embed=embed)

    @slash_subcommand(
        base='server',
        name='offline_bots'
    )
    async def check_bots(self, ctx: SlashContext):
        bots_list = [member for member in ctx.guild.members if member.bot]

        content = f'**Offline bots in {ctx.guild.name} server**\n'
        content += ', '.join(
            f'{bot.mention}' for bot in bots_list if str(bot.status) == 'offline'
        )

        await ctx.send(content=content)

    @slash_subcommand(
        base='server',
        name='role_perms'
    )
    async def guild_role_permissions(self, ctx: SlashContext, role: Role):
        description = ''.join(
            f'✅ {permission[0]}\n' if permission[1] else f'❌ {permission[0]}\n'
            for permission in role.permissions
        )

        embed = Embed(
            title=f'Server permissions for {role.name} role',
            description=description,
            color=self.bot.get_embed_color(ctx.guild_id)
        )

        await ctx.send(embed=embed)

    @slash_command(
        name='invite',
        description='Send\'s bot invite link'
    )
    async def invite_bot(self, ctx: SlashContext):
        components = [
            [
                Button(style=ButtonStyle.URL, label='Invite (No perms)', url=self.bot.no_perms_invite_link),
                Button(style=ButtonStyle.URL, label='Invite (Administrator)', url=self.bot.admin_invite_link),
                Button(style=ButtonStyle.URL, label='Invite (Recommended)', url=self.bot.recommended_invite_link)
            ]
        ]

        await ctx.send('Click on button to invite bot!', components=components)


def setup(bot):
    bot.add_cog(Misc(bot))
