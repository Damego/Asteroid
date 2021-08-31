import discord
from discord.ext import commands

from .bot_settings import is_administrator_or_bot_owner
from mongobot import MongoComponentsBot



def get_emoji_role(collection, payload, emoji):
    """Get guild emoji roles from json """
    emoji_role = collection.find_one({'_id':str(payload.message_id)})

    return emoji_role[str(emoji)]


class ReactionRole(commands.Cog, description='Роли по реакции'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '✨'


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
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


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
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


    @commands.group(
        name='reactionrole',
        aliases=['rr'],
        description='Основная команда для установления/изменения ролей по реакции',
        help='[команда]',
        usage='Только для Администрации',
        invoke_without_command=True)
    @is_administrator_or_bot_owner()
    async def reactionrole(self, ctx):
        await ctx.send(f'Используйте `{self.bot.get_guild_prefix(ctx.guild.id)}help ReactionRole` для получения информации')


    @reactionrole.group(
        name='add',
        aliases=['+', 'a'],
        description='Добавляет пост/роль',
        help='[команда]',
        usage='Только для Администрации',
        invoke_without_command=True)
    @is_administrator_or_bot_owner()
    async def add(self, ctx):
        ...


    @add.command(name='post', description='Записывает пост для выдачи роли по реакции', help='[id поста]')
    @is_administrator_or_bot_owner()
    async def add_post(self, ctx, post_id):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.insert_one({'_id':post_id})
        await ctx.message.add_reaction('✅')


    @add.command(name='role', description='Добавляет роль по реакции', help='[id поста] [эмодзи] [роль]')
    @is_administrator_or_bot_owner()
    async def add_emoji_role(self, ctx, post_id, emoji, role:discord.Role):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')

        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id':post_id},
            {'$set':{emoji:role.id}},
            upsert=True
        )

        await ctx.message.add_reaction('✅')


    @reactionrole.group(
        name='remove',
        aliases=['-', 'r'],
        description='Удаляет пост/роль',
        help='[команда]',
        usage='Только для Администрации',
        invoke_without_command=True)
    @is_administrator_or_bot_owner()
    async def remove(self, ctx):
        ...


    @remove.command(
        name='post',
        description='Удаляет пост для выдачи роли по реакции',
        help='[id поста]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def remove_post(self, ctx, post_id:int):
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.delete_one({'_id':post_id})

        await ctx.message.add_reaction('✅')


    @remove.command(
        name='role',
        description='Удаляет роль по реакции',
        help='[id поста] [эмодзи]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def remove_role(self, ctx, post_id, emoji):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')
        
        collection = self.bot.get_guild_reaction_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id':post_id},
            {'$unset':{emoji:''}}
        )

        await ctx.message.add_reaction('✅')




def setup(bot):
    bot.add_cog(ReactionRole(bot))

