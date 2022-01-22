from asyncio import TimeoutError
from datetime import datetime
import os
from typing import Union, List

import aiohttp
from discord import Member, Embed, Role, Guild, PublicUserFlags, Webhook, AsyncWebhookAdapter, TextChannel, Forbidden
from discord.ext.commands import is_owner
from discord_slash import SlashContext, ContextMenuType, MenuContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu
)
from discord_components import Button, ButtonStyle
from discord_slash_components_bridge import ComponentContext, ComponentMessage

from my_utils import AsteroidBot, get_content, Cog, CogDisabledOnGuild, is_enabled, _cog_is_enabled, transform_permission, consts
from .levels._levels import formula_of_experience


class Misc(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '💡'
        self.name = 'Misc'

        self.slash_use_channel: TextChannel = None

    async def send_guilds_update_webhooks(self, embed: Embed):
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                os.getenv('WEBHOOK_GUILDS_UPDATE'),
                adapter=AsyncWebhookAdapter(session)
            )
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

    @Cog.listener()
    async def on_slash_command(self, ctx: SlashContext):
        if self.slash_use_channel is None:
            self.slash_use_channel = self.bot.get_channel(933755239583080448)
        await self.slash_use_channel.send(
            f"{datetime.utcnow()} | **{ctx.guild.name}** | {ctx.guild_id} | **{ctx.author.display_name}**\n" \
            f"`/{self.bot.get_transformed_command_name(ctx)} {ctx.kwargs}`"
        )

    @slash_command(
        name='info',
        description='Shows information about guild member'
    )
    @is_enabled()
    async def get_member_information_slash(self, ctx: SlashContext, member: Member = None):
        embed = self._get_embed_member_info(ctx, member or ctx.author)
        await ctx.send(embed=embed)

    @context_menu(
        name='Profile',
        target=ContextMenuType.USER
    )
    @is_enabled()
    async def get_member_information_context(self, ctx: MenuContext):
        member = ctx.target_author
        embed = self._get_embed_member_info(ctx, member)
        await ctx.send(embed=embed)

    def _get_embed_member_info(self, ctx: Union[SlashContext, MenuContext], member: Member) -> Embed:
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_MEMBER_INFO', lang=lang)

        status = content['MEMBER_STATUS']
        about_text = content['ABOUT_TITLE'].format(member.display_name)
        general_info_title_text = content['GENERAL_INFO_TITLE']

        is_bot = '<:discord_bot_badge:924198977367318548>' if member.bot else ""
        user_badges = self._get_user_badges(member.public_flags)
        badges_text = f"**{content['BADGES_TEXT']}** {user_badges}" if user_badges else ""
        member_status = status.get(str(member.status))

        member_roles = [role.mention for role in member.roles if role.name != "@everyone"][::-1]
        member_roles = ', '.join(member_roles)
        role_content = f"**{content['TOP_ROLE_TEXT']}** {member.top_role.mention}" \
                       f"\n**{content['ROLES_TEXT']}** {member_roles}" if member_roles else ""

        embed = Embed(title=about_text, color=self.bot.get_embed_color(ctx.guild_id))
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f'{ctx.author.name}', icon_url=ctx.author.avatar_url)
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
            inline=False
        )

        if member.bot:
            levels_enabled = False
        else:
            try:
                levels_enabled = _cog_is_enabled(self.bot.get_cog('Levels'), ctx.guild_id)
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
            voice_time=user_voice_time / 60
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
    @is_enabled()
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
        name='role_perms',
        description='Shows a role permissions in the server'
    )
    @is_enabled()
    async def guild_role_permissions(self, ctx: SlashContext, role: Role):
        description = ''.join(
            f"✅ {transform_permission(permission[0])}\n" 
            if permission[1]
            else f"❌ {transform_permission(permission[0])}\n"
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
    @is_enabled()
    async def invite_bot(self, ctx: SlashContext):
        content = get_content('INVITE_COMMAND', lang=self.bot.get_guild_bot_lang(ctx.guild_id))

        components = [
            [
                Button(style=ButtonStyle.URL, label=content['INVITE_BUTTON_NO_PERMS'],
                       url=self.bot.no_perms_invite_link),
                Button(style=ButtonStyle.URL, label=content['INVITE_BUTTON_ADMIN'], url=self.bot.admin_invite_link),
                Button(style=ButtonStyle.URL, label=content['INVITE_BUTTON_RECOMMENDED'],
                       url=self.bot.recommended_invite_link)
            ]
        ]

        await ctx.send(content['CLICK_TO_INVITE_TEXT'], components=components)

    #@slash_subcommand(
    #    base='test',
    #    name='info',
    #    guild_ids=test_guild_id
    #)
    async def info_command(self, ctx: SlashContext, member: Member = None):
        member_roles_embed = None
        member_other_info_embed = None
        components = [
            [
                Button(
                    label='General', 
                    style=ButtonStyle.blue, 
                    custom_id='general'
                )
            ]
        ]

        general_info_embed = self._get_general_member_info(member or ctx.author)
        if member.roles:
            member_roles_embed = self._get_member_roles_info(member or ctx.author)
            components[0].append(
                Button(
                    label='Roles/Perms.',
                    style=ButtonStyle.blue,
                    custom_id='roles&perms'
                )
            )

        member_other_info_embed = self._get_member_other_info(member)
        if member_other_info_embed:
            components[0].append(
                Button(
                    label='Other Info',
                    style=ButtonStyle.blue,
                    custom_id='other'
                )
            )

        message: ComponentMessage = await ctx.send(
            embed=general_info_embed,
            components=components if len(components) > 1 else []
        )

        if not components:
            return

        while True:
            try:
                button_ctx: ComponentContext = await self.bot.wait_for(
                    'button_click',
                    check=lambda _ctx: _ctx.author_id == ctx.author_id and _ctx.message.id == message.id,
                    timeout=60
                )
            except TimeoutError:
                return await message.disable_components()

            if button_ctx.custom_id == 'general':
                await button_ctx.edit_origin(embed=general_info_embed)
            elif button_ctx.custom_id == 'roles&perms':
                await button_ctx.edit_origin(embed=member_roles_embed)
            elif button_ctx.custom_id == 'other':
                await button_ctx.edit_origin(embed=member_other_info_embed)

    def _get_general_member_info(self, member: Member):
        embed = Embed(
            title=f'Information about {member.display_name}',
            color = self.bot.get_embed_color(member.guild.id)
        )
        user_badges = self._get_user_badges(member.public_flags)
        badges = f"\n**Badges:** {user_badges}" if user_badges else ''
        
        if member.activity:
            member_activities = ", ".join([activity.name for activity in member.activities])
            activities_text = "\n**Activity:**" if len(member_activities) < 2 else "\n**Activities:**"
            activities = f"{activities_text} {member_activities}"
        else:
            activities = ''

        embed.add_field(
            name="General information",
            value=f"**Full nickname:** {member.author.name}#{member.author.discriminator}"
                  f"\n**Mention:** {member.author.mention}"
                  f"{badges}"
                  f"\n**Created at:** <t:{int(member.created_at.timestamp())}:F>"
                  f"\n**Joined at:** <t:{int(member.joined_at.timestamp())}:F>"
                  f"\n**Status:** {member.status}"
                  f"{activities}",
            inline=False
        )

        return embed

    def _get_member_roles_info(self, member: Member):
        embed = Embed(
            title=f'Information about {member.display_name}',
            color=self.bot.get_embed_color(member.guild.id)
        )
        member_roles = ', '.join(
            [role.mention for role in member.roles if role.name != "@everyone"][::-1]
        )
        embed.add_field(
            inline=False,
            name='Roles and Permissions',
            value=f"**Roles:** {member_roles}"
                  f"\n**Top Role:** {member.top_role}"
        )
        embed.add_field(
            inline=False,
            name='Permission in server',
            value=''.join(
            f'✅ {permission[0]}\n' if permission[1] else f'❌ {permission[0]}\n'
            for permission in member.guild_permissions
            )
        )

        return embed

    def _get_member_other_info(self, member: Member):
        collection = self.bot.get_guild_users_collection(member.guild.id)
        member_info = collection.find_one({'_id': member.id})
        member_leveling = member_info.get('leveling')
        
        embed = Embed(
            title=f'Information about {member.display_name}',
            color=self.bot.get_embed_color(member.guild.id)
        )
        embed.add_field(
            name="Level system",
            value=f"**Current Level:** {member_leveling['level']}"
                  f"/n**Experience:** {member_leveling['xp']}/{formula_of_experience(member_leveling['level'])}"
                  f"/n**Total Experience:** {member_leveling['xp_amount']}"
                  f"/n**Time in Voice Channel:**"
        )

        return embed

    @slash_subcommand(
        base='staff',
        name='send_message',
        guild_ids=consts.test_global_guilds_ids
    )
    @is_owner()
    async def send_message(self, ctx: SlashContext, channel_id: str, message: str):
        if not channel_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)
        channel: TextChannel = self.bot.get_channel(int(channel_id))
        try:
            await channel.send(message)
        except Forbidden:
            await ctx.send('Unable send message to this channel!')
        else:
            await ctx.send('Successfully sent!')

    @slash_subcommand(
        base='staff',
        name='get_guild_channels',
        guild_ids=consts.test_global_guilds_ids
    )
    @is_owner()
    async def get_guilds_channels(self, ctx: SlashContext, guild_id: str):
        if not guild_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)
        guild: Guild = self.bot.get_guild(int(guild_id))
        channels: List[TextChannel] = guild.channels
        channels_data = "\n".join([f"{channel.name} | {channel.id}" for channel in channels])
        embed = Embed(title=f'Channels of {guild.name}', description=channels_data)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base='staff',
        name='get_guilds',
        guild_ids=consts.test_global_guilds_ids
    )
    async def get_guilds(self, ctx: SlashContext):
        guilds = self.bot.guilds
        embed = Embed(
            title='All bot guilds',
            description='\n'.join([f"{guild.name} | {guild.id}" for guild in guilds])
        )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="staff",
        name="get_guild_roles",
        guild_ids=consts.test_global_guilds_ids
    )
    async def get_guild_roles(self, ctx: SlashContext, guild_id: str):
        if not guild_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)
        guild = self.bot.get_guild(int(guild_id))
        description = f""
        for role in guild.roles:
            description += f"{role.name} | {role.id}"
        
        embed = Embed(
            title=f'Roles of {guild.name} server',
            description=description
        )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="staff",
        name="get_guild_bot_info",
        guild_ids=consts.test_global_guilds_ids
    )
    async def get_guild_bot_info(self, ctx: SlashContext, guild_id: str):
        if not guild_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)

        guild: Guild = self.bot.get_guild(int(guild_id))
        bot: Member = guild.get_member(ctx.bot.user.id)
        embed = Embed(
            title=f"Bot information on {guild.name} server"
        )
        embed.add_field(
            name="Roles",
            value=f", ".join([f"`{role.name}`" for role in bot.roles]),
            inline=False
        )
        server_info = f"**Bot's amount:** `{len([member for member in guild.members if member.bot])}`" \
                      f"**Total members:** `{guild.member_count}`"
        embed.add_field(
            name="Server info",
            value=server_info,
            inline=False
        )

        bot_perms = ''.join(
            f"✅ {transform_permission(permission[0])}\n" 
            if permission[1]
            else f"❌ {transform_permission(permission[0])}\n"
            for permission in bot.guild_permissions
        )

        embed.add_field(
            name="Permissions",
            value=bot_perms
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
