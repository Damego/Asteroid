from discord import Embed, TextChannel, RawReactionActionEvent, Guild, Message
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from pymongo.collection import Collection

from my_utils import AsteroidBot, Cog, is_administrator_or_bot_owner


class Utilities(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
        if str(payload.emoji) != '⭐':
            return

        collection = self.bot.get_guild_configuration_collection(payload.guild_id)
        starboard_data = collection.find_one({'_id': 'starboard'})
        print(starboard_data['is_enabled'])
        if not starboard_data['is_enabled']:
            return

        guild: Guild = self.bot.get_guild(payload.guild_id)
        if payload.channel_id == starboard_data['channel_id']:
            return
        starboard_channel: TextChannel = guild.get_channel(starboard_data['channel_id'])
        channel: TextChannel = guild.get_channel(payload.channel_id)
        message: Message = await channel.fetch_message(payload.message_id)

        count = 0
        for reaction in message.reactions:
            emoji = reaction.emoji
            if emoji == '⭐':
                count = reaction.count

        limit = starboard_data['limit']
        if count < limit:
            return

        exists_messages = starboard_data.get('messages')
        if exists_messages is None:
            await self._create_message(collection, payload, message, count, starboard_channel, channel.mention)
        elif str(payload.message_id) in exists_messages:
            await self._update_message(payload, starboard_channel, starboard_data, count)
        else:
            for _message in exists_messages:
                message_data = exists_messages[_message]
                if payload.message_id == message_data['starboard_message']:
                    await self._update_message(payload, starboard_channel, starboard_data, count)
                    break
            else:
                await self._create_message(collection, payload, message, count, starboard_channel, channel.mention)

    @staticmethod
    async def _update_message(
        payload: RawReactionActionEvent,
        starboard_channel: TextChannel,
        starboard_data: dict,
        count: int
    ):
        _starboard_message_id = starboard_data['messages'][str(payload.message_id)]['starboard_message']
        starboard_message = await starboard_channel.fetch_message(_starboard_message_id)
        origin_channel_mention = starboard_message.content.split()[2]
        message_content = f'⭐{count} | {origin_channel_mention}'
        await starboard_message.edit(content=message_content)

    @staticmethod
    async def _create_message(
        collection: Collection,
        payload: RawReactionActionEvent,
        message: Message,
        count: int,
        starboard_channel: TextChannel,
        original_channel_mention: str
    ):
        if message.content == '':
            return
        embed_description = f"{message.content}\n\n" \
                            f"**[Jump to original message!]({message.jump_url})**"
        embed = Embed(
            description=embed_description,
            color=0xeee2a0
        )
        embed.set_author(
            name=payload.member,
            icon_url=payload.member.avatar_url
        )
        starboard_message = await starboard_channel.send(
            content=f'⭐{count} | {original_channel_mention}',
            embed=embed
        )
        collection.update_one(
            {'_id': 'starboard'},
            {
                '$set': {
                    f'messages.{payload.message_id}': {
                        'starboard_message': starboard_message.id
                    }
                }
            }
        )

    @slash_subcommand(
        base='starboard',
        name='channel',
        description='Starboard channel setting'
    )
    @is_administrator_or_bot_owner()
    async def set_starboard_channel(self, ctx: SlashContext, channel: TextChannel):
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        data = {
            'is_enabled': True,
            'channel_id': channel.id,
            'limit': 3
        }
        collection.update_one(
            {'_id': 'starboard'},
            {'$set': data},
            upsert=True
        )
        await ctx.send('Starboard channel was set up!')

    @slash_subcommand(
        base='starboard',
        name='limit',
        description='Limit setting'
    )
    @is_administrator_or_bot_owner()
    async def set_starboard_stars_limit(self, ctx: SlashContext, limit: int):
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'starboard'},
            {'$set': {'limit': limit}},
            upsert=True
        )
        await ctx.send(f'For now limit is {limit}')

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
    @is_administrator_or_bot_owner()
    async def set_starboard_status(self, ctx: SlashContext, status: str):
        _status = True if status == 'enable' else False
        print(status)
        print(_status)
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'starboard'},
            {'$set': {'is_enabled': _status}},
            upsert=True
        )
        await ctx.send(f'Starboard was `{status}d`')


def setup(bot):
    bot.add_cog(Utilities(bot))