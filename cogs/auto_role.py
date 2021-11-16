from discord import Role
from discord_components import Select, SelectOption
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash_components_bridge import ComponentContext, ComponentMessage

from my_utils import (
    AsteroidBot,
    get_content,
    Cog,
    bot_owner_or_permissions
)


class AutoRole(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.name = 'AutoRole'
        self.emoji = '✨'

    @Cog.listener()
    async def on_select_option(self, ctx: ComponentContext):
        if ctx.custom_id != 'autorole_select':
            return

        values = ctx.selected_options
        added_roles = []
        removed_roles = []

        for _role in values:
            role: Role = ctx.guild.get_role(int(_role))
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
                removed_roles.append(f'`{role.name}`')
            else:
                await ctx.author.add_roles(role)
                added_roles.append(f'`{role.name}`')

        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)
        message_content = ''
        if added_roles:
            message_content += content['ADDED_ROLES_TEXT'] + ', '.join(added_roles)
        if removed_roles:
            message_content += content['REMOVED_ROLES_TEXT'] + ', '.join(removed_roles)

        await ctx.send(content=message_content, hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='create',
        description='Creating new dropdown'
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def autorole_create_dropdown(
        self,
        ctx: SlashContext,
        message_content: str,
        placeholder: str = None
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)
        components = [
            Select(
                placeholder=placeholder if placeholder is not None else content['NO_OPTIONS_TEXT'],
                options=[
                    SelectOption(label='None', value='None')
                ],
                disabled=True,
                id='autorole_select'
            )
        ]

        await ctx.channel.send(content=message_content, components=components)
        await ctx.send(content['CREATED_DROPDOWN_TEXT'], hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='add_role',
        description='Adding role to dropdown'
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def autorole_dropdown_add_role(
        self,
        ctx: SlashContext,
        message_id: str,
        title: str,
        role: Role,
        emoji: str = None,
        description: str = None
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)
        original_message: ComponentMessage = await ctx.channel.fetch_message(int(message_id))
        if not original_message.components:
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'])

        select_component: Select = original_message.components[0].components[0]
        if select_component.custom_id != 'autorole_select':
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        if len(select_component.options) == 25:
            return await ctx.send(content['OPTIONS_OVERKILL_TEXT'], hidden=True)

        _emoji = emoji.split(':')
        if len(_emoji) == 3:
            _emoji = _emoji[-1].replace('>', '')
            emoji = self.bot.get_emoji(int(_emoji))

        if select_component.options[0].label == 'None':
            select_component.options = [
                SelectOption(
                    label=title,
                    value=f'{role.id}',
                    emoji=emoji,
                    description=description
                )
            ]
        else:
            select_component.options.append(
                SelectOption(
                    label=title,
                    value=f'{role.id}',
                    emoji=emoji,
                    description=description
                )
            )
        select_component.disabled = False
        if select_component.placeholder == content['NO_OPTIONS_TEXT']:
            select_component.placeholder = content['SELECT_ROLE_TEXT']

        select_component.max_values = len(select_component.options)
        await original_message.edit(components=[select_component])
        await ctx.send(content['ROLE_ADDED_TEXT'], hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='remove_role',
        description='Removing role from dropdown'
    )
    async def autorole_dropdown_remove_role(
        self,
        ctx: SlashContext,
        message_id: str,
        title: str
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)
        original_message: ComponentMessage = await ctx.channel.fetch_message(int(message_id))
        if not original_message.components:
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'])

        select_component: Select = original_message.components[0].components[0]
        if select_component.custom_id != 'autorole_select':
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        select_options = select_component.options
        for option in select_options:
            if option.label == title:
                option_index = select_options.index(option)
                del select_options[option_index]
                break
        else:
            return await ctx.send(content['OPTION_NOT_FOUND_TEXT'], hidden=True)

        if not select_options:
            return await ctx.send(content['OPTIONS_LESS_THAN_1_TEXT'], hidden=True)

        select_component.max_values = len(select_options)
        await original_message.edit(components=[select_component])
        await ctx.send(content['ROLE_REMOVED_TEXT'], hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='set_status',
        description='Set up status on dropdown',
        options=[
            create_option(
                name='message_id',
                description='ID of message with dropdown',
                required=True,
                option_type=3
            ),
            create_option(
                name='status',
                description='status of dropdown',
                required=True,
                option_type=3,
                choices=[
                    create_choice(name='enable', value='enable'),
                    create_choice(name='disable', value='disable')
                ]
            )
        ]
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def autorole_dropdown_set_status(
        self,
        ctx: SlashContext,
        message_id: str,
        status: str
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)
        original_message: ComponentMessage = await ctx.channel.fetch_message(int(message_id))
        if not original_message.components:
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'])

        select_component: Select = original_message.components[0].components[0]
        if select_component.custom_id != 'autorole_select':
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        select_component.disabled = True if status == 'disable' else False
        message_content = content['DROPDOWN_ENABLED_TEXT'] \
            if status == select_component.disabled else content['DROPDOWN_DISABLED_TEXT']

        await original_message.edit(components=[select_component])
        await ctx.send(message_content, hidden=True)


def setup(bot):
    bot.add_cog(AutoRole(bot))
