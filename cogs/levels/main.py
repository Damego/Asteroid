from time import time
from random import randint

from discord import Member, Message, VoiceState, Role, Embed
from discord_slash.utils.manage_commands import create_option
from pymongo.collection import Collection
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand

from my_utils import (
    AsteroidBot,
    bot_owner_or_permissions,
    is_enabled,
    _is_enabled,
    CogDisabledOnGuild,
    Cog,
    consts,
)
from my_utils.paginator import Paginator, PaginatorStyle
from ._levels import update_member, formula_of_experience


class Levels(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = 863677232239869964
        self.name = 'Levels'

        self.last_user_message = {}
        self.time_factor = 10

    def _get_guild_start_role(self, guild_id: int):
        guild_configuration_collection = self.bot.get_guild_configuration_collection(guild_id)
        guild_configuration = guild_configuration_collection.find_one({'_id': 'configuration'})

        if 'on_join_role' in guild_configuration:
            return guild_configuration.get('on_join_role')
        else:
            return ''

    @Cog.listener()
    async def on_member_join(self, member: Member):
        if member.bot:
            return
        try:
            _is_enabled(self, member.guild.id)
        except CogDisabledOnGuild:
            return
        await self.add_member(member)

    @Cog.listener()
    async def on_member_remove(self, member: Member):
        if member.bot:
            return
        try:
            _is_enabled(self, member.guild.id)
        except CogDisabledOnGuild:
            return
        collection = self.bot.get_guild_users_collection(member.guild.id)
        collection.delete_one({'_id': str(member.id)})

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        try:
            _is_enabled(self, member.guild.id)
        except CogDisabledOnGuild:
            return
        if member.bot:
            return

        voice_collection = self.bot.get_guild_voice_time_collection(member.guild.id)

        if (not before.channel) and after.channel:  # * If member join to channel
            members = after.channel.members
            if len(members) == 2:
                voice_collection.update_one(
                    {'_id': str(member.id)},
                    {'$set': {'voice_time': time()}},
                    upsert=True
                )

                first_member = members[0]
                if voice_collection.find_one({'_id': str(first_member.id)}) is None:
                    voice_collection.update_one(
                        {'_id': str(first_member.id)},
                        {'$set': {'voice_time': time()}},
                        upsert=True
                    )
            elif len(members) > 2:
                voice_collection.update_one(
                    {'_id': str(member.id)},
                    {'$set': {'voice_time': time()}},
                    upsert=True
                )

        elif member not in before.channel.members and (not after.channel):  # * if member left from channel
            members = before.channel.members
            if len(members) == 1:
                await self.check_time(member, voice_collection)
                first_member = members[0]
                await self.check_time(first_member, voice_collection)
            elif len(members) > 1:
                await self.check_time(member, voice_collection)
        elif member not in before.channel.members and member in after.channel.members:
            # * If member moved from one channel to another
            before_members = before.channel.members
            after_members = after.channel.members

            if len(before_members) == 0:
                if len(after_members) == 1:
                    return
                elif len(after_members) > 1:
                    if len(after_members) == 2:
                        voice_collection.update_one(
                            {'_id': str(after_members[0].id)},
                            {'$set': {'voice_time': time()}},
                            upsert=True
                        )
                    voice_collection.update_one(
                        {'_id': str(member.id)},
                        {'$set': {'voice_time': time()}},
                        upsert=True
                    )

            if len(before_members) == 1:
                await self.check_time(before_members[0], voice_collection)
            if len(after_members) == 1:
                await self.check_time(after_members[0], voice_collection)

    async def check_time(self, member: Member, voice_collection: Collection):
        try:
            voice_user = voice_collection.find_one({'_id': str(member.id)})
            sit_time = int(time()) - voice_user['voice_time']
            voice_collection.delete_one({'_id': str(member.id)})
            exp = (sit_time // 60) * self.time_factor
            await update_member(self.bot, member, exp)

            collection = self.bot.get_guild_users_collection(member.guild.id)
            user_data = collection.find_one({'_id': str(member.id)})

            if user_data.get('voice_time_count') is None:
                collection.update_one(
                    {'_id': str(member.id)},
                    {'$set': {'voice_time_count': 0}},
                    upsert=True
                )
            collection.update_one(
                {'_id': str(member.id)},
                {'$inc': {'voice_time_count': (sit_time // 60)}}
            )
        except Exception as e:
            print('[LEVELS ERROR]', e)

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        user_id = message.author.id

        users_collection = self.bot.get_guild_users_collection(message.guild.id)
        user = users_collection.find_one({'_id': str(user_id)})

        if user is None:
            await self.add_member(message.author)
        else:
            xp = randint(25, 35)
            await update_member(self.bot, message, xp)

    async def add_member(self, member: Member):
        role = self._get_guild_start_role(member.guild.id)

        collection = self.bot.get_guild_users_collection(member.guild.id)
        collection.update_one(
            {'_id': str(member.id)},
            {
                '$set': {
                    'voice_time_count': 0,
                    'leveling': {
                        'level': 1,
                        'xp': 0,
                        'xp_amount': 0,
                        'role': role
                    }
                }
            },
            upsert=True
        )

        if role != '':
            await member.add_roles(member.guild.get_role(role))

    @slash_subcommand(
        base='levels',
        name='reset_stats',
        description='Reset levels statistics of Member',
        options=[
            create_option(
                name='member',
                description='Guild Member',
                option_type=6,
                required=True
            
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def reset_member_statistics(self, ctx: SlashContext, member: Member):
        user_id = str(member.id)
        users_collection = self.bot.get_guild_users_collection(ctx.guild_id)
        user_stats = users_collection.find_one({'_id': user_id})

        current_role = ctx.guild.get_role(user_stats['leveling']['role'])
        if current_role:
            await member.remove_roles(current_role)
        role_id = self._get_guild_start_role(ctx.guild_id)

        users_collection.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'voice_time_count': 0,
                    'leveling': {
                        'level': 1,
                        'xp': 0,
                        'xp_amount': 0,
                        'role': role_id
                    }
                }
            },
            upsert=True
        )
    
        if role_id:
            await ctx.author.add_roles(ctx.guild.get_role(int(role_id)))

        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        name='xp',
        description='Add exp to member',
        options=[
            create_option(
                name='member',
                description='Server Member',
                option_type=6,
                required=True
            ),
            create_option(
                name='exp',
                description='Exp to add',
                option_type=4,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_add_xp(self, ctx: SlashContext, member: Member, exp: int):
        await ctx.defer(hidden=True)
        await update_member(self.bot, member, exp)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        name='add',
        description='Add Role to level',
        options=[
            create_option(
                name='level',
                description='level',
                option_type=4,
                required=True
            ),
            create_option(
                name='role',
                description='Role to level',
                option_type=8,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def add_level_role(self, ctx: SlashContext, level: int, role: Role):
        collection = self.bot.get_guild_level_roles_collection(ctx.guild_id)
        collection.update_one(
            {'_id': str(level)},
            {'$set': {'role_id': role.id}},
            upsert=True)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        name='remove',
        description='Remove Role of a level',
        options=[
            create_option(
                name='level',
                description='level',
                option_type=3,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def remove_level_role(self, ctx: SlashContext, level: str):
        level_roles_collection = self.bot.get_guild_level_roles_collection(ctx.guild_id)
        try:
            level_roles_collection.delete_one({'_id': level})
            await ctx.send('✅', hidden=True)
        except Exception:
            await ctx.send('❌', hidden=True)

    @slash_subcommand(
        base='levels',
        name='replace',
        description='Replace level to another',
        options=[
            create_option(
                name='current_level',
                description='current_level',
                option_type=3,
                required=True
            ),
            create_option(
                name='new_level',
                description='new_level',
                option_type=3,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def replace_level_role(self, ctx: SlashContext, old_level: str, new_level: str):
        level_roles_collection = self.bot.get_guild_level_roles_collection(ctx.guild_id)
        role = level_roles_collection.find_one_and_delete({'_id': old_level})['role_id']
        level_roles_collection.update_one(
            {'_id': new_level},
            {'$set': {'role_id': role}},
            upsert=True)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        name='reset',
        description='Reset levels in server',
        options=[]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def reset_levels(self, ctx: SlashContext):
        level_roles_collection = self.bot.get_guild_level_roles_collection(ctx.guild_id)
        level_roles_collection.drop_indexes()
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        name='list',
        description='Show list of levels in server',
        options=[]
    )
    @is_enabled
    async def send_levels_list(self, ctx: SlashContext):
        collection = self.bot.get_guild_level_roles_collection(ctx.guild_id)
        dict_levels = collection.find()

        content = ''
        
        for level in dict_levels:
            xp_amount = 0
            role = ctx.guild.get_role(level['role_id'])
            for _level in range(1, int(level['_id'])):
                exp = formula_of_experience(_level)
                xp_amount += exp
            content += f'{level["_id"]} — {role.mention} | EXP: {xp_amount}\n'

        if content == '':
            content = 'No levels roles!'

        embed = Embed(description=content, color=self.bot.get_embed_color(ctx.guild_id))
        await ctx.send(embed=embed)

    @slash_subcommand(
        base='levels',
        subcommand_group='set',
        name='role',
        description='Set role to member',
        options=[
            create_option(
                name='member',
                description='Server Member',
                option_type=6,
                required=True
            ),
            create_option(
                name='role',
                description='Role to level',
                option_type=8,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def set_role_to_member(self, ctx: SlashContext, member: Member, role: Role):
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        collection.update_one(
            {'_id': str(member.id)},
            {
                '$set': {
                    'leveling.role': role.id
                }
            }
        )
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        subcommand_group='set',
        name='time',
        description='Set voice time to member',
        options=[
            create_option(
                name='member',
                description='Server Member',
                option_type=6,
                required=True
            ),
            create_option(
                name='time',
                description='time in voice channel',
                option_type=4,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def set_time_to_member(self, ctx: SlashContext, member: Member, time: int):
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        collection.update_one(
            {'_id': str(member.id)},
            {
                '$set': {
                    'voice_time_count': time
                }
            }
        )
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        subcommand_group='set',
        name='level',
        description='Set level to member',
        options=[
            create_option(
                name='member',
                description='Server Member',
                option_type=6,
                required=True
            ),
            create_option(
                name='level',
                description='Level',
                option_type=4,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def set_level_to_member(self, ctx: SlashContext, member: Member, level: int):
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        collection.update_one(
            {'_id': str(member.id)},
            {'$set': {
                'leveling.level': level
            }
            }
        )
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        subcommand_group='on_join_role',
        name='add',
        description='Add on join role',
        options=[
            create_option(
                name='role',
                description='Role to level',
                option_type=8,
                required=True
            )
        ]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def set_on_join_role(self, ctx: SlashContext, role: Role):
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'configuration'},
            {'$set': {'on_join_role': role.id}},
            upsert=True)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        subcommand_group='on_join_role',
        name='remove',
        description='Remove on join role',
        options=[]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def set_on_join_role_remove(self, ctx: SlashContext):
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'configuration'},
            {'$unset': 'on_join_role'},
        )
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='levels',
        name='add_start_role',
        description='Add to everyone start role of guild',
        options=[]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def add_start_role(self, ctx: SlashContext):
        guild_configuration_collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        try:
            role_id = guild_configuration_collection.find_one({'_id': 'configuration'})['on_join_role']
            role = ctx.guild.get_role(role_id)
        except Exception as e:
            print('adr', e)
            return

        guild_users_collection = self.bot.get_guild_users_collection(ctx.guild_id)

        members = ctx.guild.members
        for member in members:
            if member.bot:
                continue

            current_role = guild_users_collection.find_one({'_id': str(member.id)})['leveling']['role']
            if current_role is None:
                await self.add_member(member)
                continue
            
            if current_role == '':
                guild_users_collection.update_one(
                    {'_id': str(member.id)},
                    {'$set': {'leveling.role': role_id}}
                )
                await member.add_roles(role)

    @slash_subcommand(
        base='levels',
        name='clear_members_stats',
        options=[]
    )
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def clear_members_stats(self, ctx: SlashContext):
        members = ctx.guild.members
        guild_configuration_collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        guild_users_collection = self.bot.get_guild_users_collection(ctx.guild_id)

        configuration = guild_configuration_collection.find_one({'_id': 'configuration'})
        role = configuration.get('on_join_role')
        if role is None:
            role = ''

        for member in members:
            if member.bot:
                continue

            guild_users_collection.update_one(
                {'_id': str(member.id)},
                {
                    '$set': {
                        'leveling.level': 1,
                        'leveling.xp': 0,
                        'leveling.xp_amount': 0,
                        'leveling.role': role
                    }
                }
            )

            if role:
                await member.add_roles(ctx.guild.get_role(int(role)))

        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='test',
        name='top',
        description='Shows top members by level',
        options=[],
        guild_ids=consts.test_global_guilds_ids
    )
    @is_enabled
    async def levels_top_members(self, ctx: SlashContext):
        await ctx.defer()

        embeds = []
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        users = collection.find({})
        embed_desc = f"Member | Level\n"
        raw_data = {}
        for user_data in users:
            user_leveling = user_data.get('leveling')
            if user_leveling is None:
                continue
            if user_leveling['level'] == 0:
                continue

            raw_data[user_data['_id']] = user_leveling['level']

        _list = list(raw_data.items())
        _list.sort(key=lambda i: i[1], reverse=True)
        data = dict(_list)

        for count, user_data in enumerate(data):
            member: Member = ctx.guild.get_member(user_data)
            if member is None:
                try:
                    member: Member = await ctx.guild.fetch_member(user_data)
                except Exception:
                    continue

            embed_desc += f"{count}. {member.display_name} | {data[user_data]}\n"

            if count % 10 == 0:
                embeds.append(
                    Embed(
                        title='Top members by level',
                        description=embed_desc,
                        color=self.bot.get_embed_color(ctx.guild_id)
                    )
                )
                embed_desc = f""

        if embed_desc:
            embeds.append(
                Embed(
                    title='Top members by levels',
                    description=embed_desc,
                    color=self.bot.get_embed_color(ctx.guild_id)
                )
            )

        if not embeds:
            return await ctx.send('no top')
        if len(embeds) < 2:
            return await ctx.send(embed=embeds[0])

        paginator = Paginator(self.bot, ctx, style=PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds=embeds)
        await paginator.start()

