import discord
from discord import RawReactionActionEvent
from discord.ext.commands import Cog
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand
)
from discord_slash.utils.manage_commands import create_option

from my_utils import AsteroidBot, is_administrator_or_bot_owner, is_enabled, _is_enabled, CogDisabledOnGuild
from .settings import guild_ids


def get_emoji_role(collection, payload, emoji):
    """Get guild emoji roles from json """
    emoji_role = collection.find_one({'_id':str(payload.message_id)})

    return emoji_role[str(emoji)]


class ReactionRole(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '✨'
        self.name = 'reactionrole'


    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
        try:
            _is_enabled(self, payload)
        except CogDisabledOnGuild:
            return

        collection = self.bot.get_guild_reaction_roles_collection(payload.guild_id)
        post = collection.find_one({'_id':str(payload.message_id)})
        if post is None:
            return
        emoji = payload.emoji.id
        if payload.emoji.id is None:
            emoji = payload.emoji

        role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=get_emoji_role(collection, payload, emoji))
        await payload.member.add_roles(role)


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        try:
            _is_enabled(self, payload)
        except CogDisabledOnGuild:
            return

        collection = self.bot.get_guild_reaction_roles_collection(payload.guild_id)
        post = collection.find_one({'_id':str(payload.message_id)})
        if post is None:
            return
        
        emoji = payload.emoji.id
        if payload.emoji.id is None:
            emoji = payload.emoji

        role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=get_emoji_role(collection, payload, emoji))
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            self.bot.fetch_guild(payload.guild_id)
        
        member = guild.get_member(payload.user_id)
        if member is None:
            member = guild.fetch_member(payload.user_id)
        await member.remove_roles(role)


    @slash_subcommand(
        base='reactionrole',
        subcommand_group='add',
        name='post',
        guild_ids=guild_ids,
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
    @is_administrator_or_bot_owner()
    async def add_post(self, ctx, message_id):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.insert_one({'_id':message_id})

        await ctx.send('✅', hidden=True)


    @slash_subcommand(
        base='reactionrole',
        subcommand_group='add',
        name='role',
        guild_ids=guild_ids,
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
    @is_administrator_or_bot_owner()
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
        guild_ids=guild_ids,
        options=[
            create_option(
                name='message_id',
                description='Message id',
                option_type=3,
                required=True
            ),
        ]
    )
    @is_administrator_or_bot_owner()
    @is_enabled
    async def remove_post(self, ctx, message_id):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.delete_one({'_id': message_id})

        await ctx.send('✅', hidden=True)


    @slash_subcommand(
        base='reactionrole',
        subcommand_group='remove',
        name='role',
        guild_ids=guild_ids,
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
    @is_administrator_or_bot_owner()
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

