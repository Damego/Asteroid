import datetime

from discord import Embed, TextChannel, RawReactionActionEvent, Guild, Message, Member, Role
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from pymongo.collection import Collection

from my_utils import AsteroidBot, Cog, bot_owner_or_permissions, get_content, consts


class Utilities(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = '🧰'
        self.name = 'Utilities'

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
        if str(payload.emoji) != '⭐':
            return

        collection = self.bot.get_guild_configuration_collection(payload.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if starboard_data is None:
            return
        if not starboard_data['is_enabled']:
            return
        if payload.channel_id == starboard_data['channel_id']:
            return

        guild: Guild = self.bot.get_guild(payload.guild_id)
        channel: TextChannel = guild.get_channel(payload.channel_id)
        message: Message = await channel.fetch_message(payload.message_id)
        if self._is_blacklisted(payload, message, starboard_data):
            return

        stars_count = 0
        for reaction in message.reactions:
            emoji = reaction.emoji
            if emoji == '⭐':
                stars_count = reaction.count
        limit = starboard_data['limit']
        if stars_count < limit:
            return

        starboard_channel: TextChannel = guild.get_channel(starboard_data['channel_id'])
        exists_messages = starboard_data.get('messages')
        if (
            exists_messages is None
            or str(payload.message_id) not in exists_messages
        ):
            await self._send_starboard_message(collection, message, stars_count, starboard_channel)
        else:
            starboard_message_id = starboard_data['messages'][str(payload.message_id)]['starboard_message']
            await self._update_starboard_message(starboard_channel, starboard_message_id, stars_count)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if str(payload.emoji) != '⭐':
            return

        collection = self.bot.get_guild_configuration_collection(payload.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if starboard_data is None:
            return
        if not starboard_data['is_enabled']:
            return
        if payload.channel_id == starboard_data['channel_id']:
            return

        guild: Guild = self.bot.get_guild(payload.guild_id)
        channel: TextChannel = guild.get_channel(payload.channel_id)
        message: Message = await channel.fetch_message(payload.message_id)

        if self._is_blacklisted(payload, message, starboard_data):
            return

        stars_count = 0
        for reaction in message.reactions:
            emoji = reaction.emoji
            if emoji == '⭐':
                stars_count = reaction.count

        starboard_channel: TextChannel = guild.get_channel(starboard_data['channel_id'])
        starboard_message_id = starboard_data['messages'][str(payload.message_id)]['starboard_message']
        await self._update_starboard_message(starboard_channel, starboard_message_id, stars_count)

    @staticmethod
    def _is_blacklisted(payload: RawReactionActionEvent, message: Message, starboard_data: dict):
        blacklist = starboard_data.get('blacklist')
        if not blacklist:
            return False
        blacklisted_channels = blacklist.get('channels')
        blacklisted_roles = blacklist.get('roles')
        blacklisted_members = blacklist.get('members')
        member_roles = message.guild.get_member(payload.user_id).roles
        has_blacklisted_roles = [role for role in member_roles if role.id in blacklisted_roles]
        message_author_has_blacklisted_roles = [role for role in message.author.roles if role.id in blacklisted_roles]

        if (
                blacklisted_channels and payload.channel_id in blacklisted_channels
                or blacklisted_members and (
                payload.user_id in blacklisted_members
                or message.author.id in blacklisted_members
                )
                or has_blacklisted_roles or message_author_has_blacklisted_roles
        ):
            return True

    @staticmethod
    async def _update_starboard_message(
        starboard_channel: TextChannel,
        starboard_message_id: int,
        stars_count: int
    ):
        starboard_message = await starboard_channel.fetch_message(starboard_message_id)
        origin_channel_mention = starboard_message.content.split()[2]
        message_content = f'⭐{stars_count} | {origin_channel_mention}'
        await starboard_message.edit(content=message_content)

    async def _send_starboard_message(
        self,
        collection: Collection,
        message: Message,
        stars_count: int,
        starboard_channel: TextChannel
    ):
        lang = self.bot.get_guild_bot_lang(message.guild.id)
        content = get_content('STARBOARD_FUNCTIONS', lang)
        embed_description = f"{message.content}\n\n" \
                            f"**[{content['JUMP_TO_ORIGINAL_MESSAGE_TEXT']}]({message.jump_url})**"
        embed = Embed(
            description=embed_description,
            color=0xeee2a0,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(
            name=message.author,
            icon_url=message.author.avatar_url
        )
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        starboard_message = await starboard_channel.send(
            content=f'⭐{stars_count} | {message.channel.mention}',
            embed=embed
        )

        collection.update_one(
            {'_id': 'starboard'},
            {
                '$set': {
                    f'messages.{message.id}.starboard_message': starboard_message.id
                }
            }
        )

    @slash_subcommand(
        base='starboard',
        name='channel',
        description='Starboard channel setting'
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_channel(self, ctx: SlashContext, channel: TextChannel):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('STARBOARD_FUNCTIONS', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if starboard_data is None:
            data = {
                'is_enabled': True,
                'channel_id': channel.id,
                'limit': 3
            }
        else:
            data = {
                'channel_id': channel.id
            }
        collection.update_one(
            {'_id': 'starboard'},
            {'$set': data},
            upsert=True
        )
        await ctx.send(content['CHANNEL_WAS_SETUP_TEXT'])

    @slash_subcommand(
        base='starboard',
        name='limit',
        description='Limit setting'
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_stars_limit(self, ctx: SlashContext, limit: int):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('STARBOARD_FUNCTIONS', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'starboard'},
            {'$set': {'limit': limit}},
            upsert=True
        )
        await ctx.send(content['LIMIT_WAS_SETUP_TEXT'].format(limit=limit))

    @slash_subcommand(
        base='starboard',
        name='status',
        description='Enable/disable starboard',
        options=[
            create_option(
                name='status',
                description='enable or disable starboard',
                option_type=3,
                required=True,
                choices=[
                    create_choice(
                        name='enable',
                        value='enable'
                    ),
                    create_choice(
                        name='disable',
                        value='disable'
                    )
                ]
            )
        ]
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_status(self, ctx: SlashContext, status: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('STARBOARD_FUNCTIONS', lang)

        _status = status == 'enable'
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if (
            starboard_data is None
            or 'channel_id' not in starboard_data
            or 'limit' not in starboard_data
        ):
            return await ctx.send(content['STARBOARD_NOT_SETUP_TEXT'])

        collection.update_one(
            {'_id': 'starboard'},
            {'$set': {'is_enabled': _status}},
            upsert=True
        )
        if _status:
            message_content = content['STARBOARD_ENABLED_TEXT']
        else:
            message_content = content['STARBOARD_DISABLED_TEXT']

        await ctx.send(message_content)

    @slash_subcommand(
        base='starboard',
        subcommand_group='blacklist',
        name='add',
        description='Adds member, role or channel in blacklist'
    )
    async def starboard_blacklist_add(
        self,
        ctx: SlashContext,
        member: Member = None,
        role: Role = None,
        channel: TextChannel = None
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('STARBOARD_FUNCTIONS', lang)

        if not member and not role and not channel:
            return await ctx.send(content['BLACKLIST_NO_OPTIONS_TEXT'], hidden=True)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if starboard_data is None:
            return await ctx.send(content['STARBOARD_NOT_SETUP_TEXT'], hidden=True)

        data = {}
        if 'blacklist' not in starboard_data:
            if member:
                data['members'] = member.id
            if role:
                data['roles'] = role.id
            if channel:
                data['channels'] = channel.id
        else:
            blacklist = starboard_data['blacklist']
            if member and member.id not in blacklist['members']:
                data['members'] = member.id
            if role and role.id not in blacklist['roles']:
                data['roles'] = role.id
            if channel and channel.id not in blacklist['channels']:
                data['channels'] = channel.id

        to_send = {f'blacklist.{key}': value for key, value in data.items()}

        collection.update_one(
            {'_id': 'starboard'},
            {
                '$push': to_send
            },
            upsert=True
        )

        await ctx.send(content['BLACKLIST_ADDED_TEXT'], hidden=True)

    @slash_subcommand(
        base='starboard',
        subcommand_group='blacklist',
        name='remove',
        description='Removes member/role/channel from blacklist'
    )
    async def starboard_blacklist_remove(
        self,
        ctx: SlashContext,
        member: Member = None,
        role: Role = None,
        channel: TextChannel = None
    ):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('STARBOARD_FUNCTIONS', lang)

        if not member and not role and not channel:
            return await ctx.send(content['BLACKLIST_NO_OPTIONS_TEXT'])

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if starboard_data is None:
            return await ctx.send(content['STARBOARD_NOT_SETUP_TEXT'], hidden=True)

        data = {}
        if 'blacklist' not in starboard_data:
            return await ctx.send(content['EMPTY_BLACKLIST_TEXT'], hidden=True)

        blacklist = starboard_data['blacklist']
        if member and member.id in blacklist['members']:
            data['members'] = member.id
        if role and role.id in blacklist['roles']:
            data['roles'] = role.id
        if channel and channel.id in blacklist['channels']:
            data['channels'] = channel.id

        to_send = {f'blacklist.{key}': value for key, value in data.items()}

        collection.update_one(
            {'_id': 'starboard'},
            {
                '$pull': to_send
            },
            upsert=True
        )

        await ctx.send(content['BLACKLIST_REMOVED_TEXT'], hidden=True)

    @slash_subcommand(
        base='starboard',
        subcommand_group='blacklist',
        name='list',
        description='Shows blacklist'
    )
    async def starboard_blacklist_list(self, ctx: SlashContext, hidden: bool = False):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('STARBOARD_FUNCTIONS', lang)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        if starboard_data is None:
            return await ctx.send(content['STARBOARD_NOT_SETUP_TEXT'], hidden=True)
        if 'blacklist' not in starboard_data or not starboard_data['blacklist']:
            return await ctx.send(content['EMPTY_BLACKLIST_TEXT'], hidden=True)

        embed = Embed(
            title=content['BLACKLIST_TEXT'],
            color=self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.datetime.utcnow()
        )
        members = starboard_data['blacklist'].get('members')
        channels = starboard_data['blacklist'].get('channels')
        roles = starboard_data['blacklist'].get('roles')

        if not members and not channels and not roles:
            return await ctx.send(content['EMPTY_BLACKLIST_TEXT'], hidden=True)
        if members:
            embed.add_field(
                name=content['MEMBERS'],
                value=', '.join([f'<@{user_id}>' for user_id in members]),
                inline=False
            )
        if channels:
            embed.add_field(
                name=content['CHANNELS'],
                value=', '.join([f'<#{channel_id}>' for channel_id in channels]),
                inline=False
            )
        if roles:
            embed.add_field(
                name=content['ROLES'],
                value=', '.join([f'<@&{role_id}>' for role_id in roles]),
                inline=False
            )

        await ctx.send(embed=embed, hidden=hidden)


def setup(bot):
    bot.add_cog(Utilities(bot))
