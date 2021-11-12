import discord
from discord import RawReactionActionEvent
from discord_slash.cog_ext import (
    cog_subcommand as slash_subcommand
)
from discord_slash.utils.manage_commands import create_option

from my_utils import (
    AsteroidBot,
    bot_owner_or_permissions,
    is_enabled, _is_enabled,
    CogDisabledOnGuild,
    Cog
)


def get_emoji_role(collection, message_id: int, emoji):
    emoji_role = collection.find_one({'_id':str(message_id)})

    return emoji_role[str(emoji)]


class ReactionRole(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = '✨'
        self.name = 'ReactionRole'

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
        try:
            _is_enabled(self, payload.guild_id)
        except CogDisabledOnGuild:
            return

        collection = self.bot.get_guild_reaction_roles_collection(payload.guild_id)
        post = collection.find_one({'_id':str(payload.message_id)})
        if post is None:
            return
        emoji = payload.emoji.id
        if payload.emoji.id is None:
            emoji = payload.emoji

        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(payload.guild_id)

        emoji_role = get_emoji_role(collection, payload.message_id, emoji)
        role = guild.get_role(emoji_role)

        await payload.member.add_roles(role)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        try:
            _is_enabled(self, payload.guild_id)
        except CogDisabledOnGuild:
            return

        collection = self.bot.get_guild_reaction_roles_collection(payload.guild_id)
        post = collection.find_one({'_id':str(payload.message_id)})
        if post is None:
            return
        
        emoji = payload.emoji.id
        if payload.emoji.id is None:
            emoji = payload.emoji

        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
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
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def add_post(self, ctx, message_id):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.insert_one({'_id':message_id})

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
    @is_enabled
    @bot_owner_or_permissions(manage_guild=True)
    async def add_emoji_role(self, ctx, message_id, emoji, role:discord.Role):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')

        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id': message_id},
            {'$set':{emoji:role.id}},
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
    @bot_owner_or_permissions(manage_guild=True)
    @is_enabled
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
    @bot_owner_or_permissions(manage_guild=True)
    @is_enabled
    async def remove_role(self, ctx, message_id, emoji):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')
        
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id':message_id},
            {'$unset':{emoji:''}}
        )

        await ctx.send('✅', hidden=True)


def setup(bot):
    bot.add_cog(ReactionRole(bot))

