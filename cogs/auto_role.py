from discord import Role, Embed, RawReactionActionEvent, Guild, Member
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_components import Select, SelectOption
from discord_slash_components_bridge import ComponentContext, ComponentMessage

from my_utils import (
    AsteroidBot,
    get_content,
    Cog,
    bot_owner_or_permissions,
    is_enabled, _cog_is_enabled,
    CogDisabledOnGuild,
)


def get_emoji_role(collection, message_id: int, emoji):
    emoji_role = collection.find_one({'_id': str(message_id)})

    return emoji_role[str(emoji)]


class AutoRole(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.name = 'AutoRole'
        self.emoji = '✨'

    # ON JOIN ROLE
    @Cog.listener()
    async def on_member_join(self, member: Member):
        if member.bot:
            return

        collection = self.bot.get_guild_configuration_collection(member.guild.id)
        config = collection.find_one({'_id': 'configuration'})
        on_join_roles = config.get('on_join_roles')
        if on_join_roles is None:
            return
        guild = member.guild
        for role_id in on_join_roles:
            role: Role = guild.get_role(role_id)
            await member.add_roles(role)

    @slash_subcommand(
        base='autorole',
        subcommand_group='on_join',
        name='add',
        description='Adds a new on join role'
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def autorole_on_join_add(self, ctx: SlashContext, role: Role):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_ON_JOIN', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'configuration'},
            {
                '$push': {
                    'on_join_roles': role.id
                }
            }
        )

        await ctx.send(content['ROLE_ADDED_TEXT'].format(role=role.mention))

    @slash_subcommand(
        base='autorole',
        subcommand_group='on_join',
        name='remove',
        description='Removes on join role'
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def autorole_on_join_remove(self, ctx: SlashContext, role: Role):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_ON_JOIN', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'configuration'},
            {
                '$pull': {
                    'on_join_roles': role.id
                }
            }
        )

        await ctx.send(content['ROLE_REMOVED_TEXT'].format(role=role.mention))

    # SELECT ROLE

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
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
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
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
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
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        select_component: Select = original_message.components[0].components[0]
        if select_component.custom_id != 'autorole_select':
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        if len(select_component.options) == 25:
            return await ctx.send(content['OPTIONS_OVERKILL_TEXT'], hidden=True)

        if emoji:
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
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
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
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
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
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        select_component: Select = original_message.components[0].components[0]
        if select_component.custom_id != 'autorole_select':
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        select_component.disabled = status == 'disable'
        message_content = content['DROPDOWN_ENABLED_TEXT'] \
            if status == select_component.disabled else content['DROPDOWN_DISABLED_TEXT']

        await original_message.edit(components=[select_component])
        await ctx.send(message_content, hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='save',
        description='Save dropdown to database'
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def autorole_dropdown_save(
            self,
            ctx: SlashContext,
            message_id: str,
            name: str
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)

        original_message: ComponentMessage = await ctx.channel.fetch_message(int(message_id))
        if not original_message.components:
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        select_component: Select = original_message.components[0].components[0]
        if select_component.custom_id != 'autorole_select':
            return await ctx.send(content['MESSAGE_WITHOUT_DROPDOWN_TEXT'], hidden=True)

        data = {
            'content': original_message.content,
            'component': select_component.to_dict()
        }

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'autorole'},
            {
                '$set': {
                    name: data
                }
            },
            upsert=True
        )

        await ctx.send(content['DROPDOWN_SAVED_TEXT'], hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='load',
        description='Load dropdown from database and send this'
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def autorole_dropdown_load(self, ctx: SlashContext, name: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        autorole_data = collection.find_one({'_id': 'autorole'})
        if autorole_data is None:
            return await ctx.send(content['NOT_SAVED_DROPDOWNS'])
        message_data = autorole_data.get(name)
        if message_data is None:
            return await ctx.send(content['DROPDOWN_NOT_FOUND'])

        select_component = Select.from_json(message_data['component'])

        await ctx.channel.send(content=message_data['content'], components=[select_component])
        await ctx.send(content['DROPDOWN_LOADED_TEXT'], hidden=True)

    @slash_subcommand(
        base='autorole',
        subcommand_group='dropdown',
        name='list',
        description='Show list of saved dropdowns'
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def autorole_dropdown_list(self, ctx: SlashContext):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('AUTOROLE_DROPDOWN', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        autorole_data = collection.find_one({'_id': 'autorole'})
        if autorole_data is None:
            return await ctx.send(content['NOT_SAVED_DROPDOWNS'])

        embed = Embed(
            title=content['DROPDOWN_LIST'],
            description='',
            color=self.bot.get_embed_color(ctx.guild_id)
        )

        del autorole_data['_id']
        for count, dropdown in enumerate(autorole_data, start=1):
            embed.description += f'**{count}. {dropdown}**\n'

        await ctx.send(embed=embed, hidden=True)

    # REACTION ROLE COMMANDS AND EVENTS
    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
        try:
            _cog_is_enabled(self, payload.guild_id)
        except CogDisabledOnGuild:
            return

        collection = self.bot.get_guild_reaction_roles_collection(payload.guild_id)
        post = collection.find_one({'_id': str(payload.message_id)})
        if post is None:
            return
        emoji = payload.emoji.id
        if payload.emoji.id is None:
            emoji = payload.emoji

        guild: Guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(payload.guild_id)

        emoji_role = get_emoji_role(collection, payload.message_id, emoji)
        role = guild.get_role(emoji_role)

        await payload.member.add_roles(role)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        try:
            _cog_is_enabled(self, payload.guild_id)
        except CogDisabledOnGuild:
            return

        collection = self.bot.get_guild_reaction_roles_collection(payload.guild_id)
        post = collection.find_one({'_id': str(payload.message_id)})
        if post is None:
            return

        emoji = payload.emoji.id
        if payload.emoji.id is None:
            emoji = payload.emoji

        guild: Guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(payload.guild_id)

        emoji_role = get_emoji_role(collection, payload.message_id, emoji)
        role = guild.get_role(emoji_role)

        member = guild.get_member(payload.user_id)
        if member is None:
            member = guild.fetch_member(payload.user_id)
        await member.remove_roles(role)

    @slash_subcommand(
        base='reactionrole',
        subcommand_group='add',
        name='post',
        description='Adds new message to react',
        options=[
            create_option(
                name='message_id',
                description='Message id',
                option_type=3,
                required=True
            )
        ]
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def add_post(self, ctx, message_id):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.insert_one({'_id': message_id})

        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='reactionrole',
        subcommand_group='add',
        name='role',
        description='Add reaction role to message',
        options=[
            create_option(
                name='message_id',
                description='Message id',
                option_type=3,
                required=True
            ),
            create_option(
                name='emoji',
                description='emoji or emoji id',
                option_type=3,
                required=True
            ),
            create_option(
                name='role',
                description='role for emoji',
                option_type=8,
                required=True
            ),
        ]
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_roles=True)
    async def add_emoji_role(self, ctx, message_id, emoji, role: Role):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>', '')

        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id': message_id},
            {'$set': {emoji: role.id}},
            upsert=True
        )

        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='reactionrole',
        subcommand_group='remove',
        name='post',
        description='Remove\'s message to react',
        options=[
            create_option(
                name='message_id',
                description='Message id',
                option_type=3,
                required=True
            ),
        ]
    )
    @bot_owner_or_permissions(manage_roles=True)
    @is_enabled()
    async def remove_post(self, ctx, message_id):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.delete_one({'_id': message_id})

        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='reactionrole',
        subcommand_group='remove',
        name='role',
        description='Remove reaction role from message',
        options=[
            create_option(
                name='message_id',
                description='Message id',
                option_type=3,
                required=True
            ),
            create_option(
                name='emoji',
                description='emoji or emoji id',
                option_type=3,
                required=True
            )
        ]
    )
    @bot_owner_or_permissions(manage_roles=True)
    @is_enabled()
    async def remove_role(self, ctx, message_id, emoji):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>', '')

        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id': message_id},
            {'$unset': {emoji: ''}}
        )

        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='autorole',
        name='add_role_to_everyone',
        description='Adds role to everyone member on server'
    )
    async def autorole_add_role_to_everyone(self, ctx: SlashContext, role: Role):
        await ctx.defer()
        for member in ctx.guild.members:
            if role not in member.roles:
                await member.add_roles(role)
        await ctx.send('☑️', hidden=True)

    @slash_subcommand(
        base='autorole',
        name='remove_role_from_everyone',
        description='Removes role from everyone member on server'
    )
    async def autorole_remove_role_from_everyone(self, ctx: SlashContext, role: Role):
        await ctx.defer()
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_roles(role)
        await ctx.send('☑️', hidden=True)


def setup(bot):
    bot.add_cog(AutoRole(bot))
