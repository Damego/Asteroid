import discord
from discord.ext import commands

from extensions.bot_settings import get_db, get_prefix

server = get_db()

def get_react_post_id(guild_id):
    """Get guild react post id from json """
    return server[str(guild_id)]['reaction_posts']

def get_emoji_role(payload, emoji):
    """Get guild emoji roles from json """
    return server[str(payload.guild_id)]['reaction_posts'][str(payload.message_id)][str(emoji)]


class ReactionRole(commands.Cog, description='Роль по реакции'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['reactionrole', 'rr', 'react']


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.member.bot:
            posts = get_react_post_id(payload.guild_id)
            if str(payload.message_id) in posts:
                emoji = payload.emoji.id
                if payload.emoji.id is None:
                    emoji = payload.emoji

                role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=get_emoji_role(payload, emoji))
                await payload.member.add_roles(role)
    

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        posts = get_react_post_id(payload.guild_id)
        if str(payload.message_id) in posts:
            emoji = payload.emoji.id
            if payload.emoji.id is None:
                emoji = payload.emoji

            role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=get_emoji_role(payload, emoji))
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            await member.remove_roles(role)


    @commands.group(
        name='reactionrole',
        aliases=['rr'],
        description='',
        help='[команда]',
        usage='Только для Администрации',
        invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def reactionrole(self, ctx):
        await ctx.send(f'Используйте `{get_prefix(ctx.guild.id)}help ReactionRole` для получения информации')


    @reactionrole.group(
        name='add',
        aliases=['+', 'a'],
        description='',
        help='[команда]',
        usage='Только для Администрации',
        invoke_without_command=True,
        hidden=True)
    @commands.has_guild_permissions(administrator=True)
    async def add(self, ctx):
        ...


    @add.command(name='post', description='Записывает пост для выдачи роли по реакции', help='[id поста]')
    @commands.has_guild_permissions(administrator=True)
    async def post(ctx, post_id):
        server[str(ctx.guild.id)]['reaction_posts'][post_id] = {}
        await ctx.message.add_reaction('✅')


    @add.command(name='role', description='Добавляет роль по реакции', help='[id поста] [эмодзи] [роль]')
    @commands.has_guild_permissions(administrator=True)
    async def role(ctx, post_id, emoji, role:discord.Role):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')

        server[str(ctx.guild.id)]['reaction_posts'][str(post_id)][str(emoji)] = role.id

        await ctx.message.add_reaction('✅')


    @reactionrole.group(
        name='remove',
        aliases=['-', 'r'],
        description='',
        help='[команда]',
        usage='Только для Администрации',
        invoke_without_command=True,
        hidden=True)
    @commands.has_guild_permissions(administrator=True)
    async def remove(self, ctx):
        ...


    @remove.command(
        name='post',
        description='Удаляет пост для выдачи роли по реакции',
        help='[id поста]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def post(ctx, post_id:int):
        del server[str(ctx.guild.id)]['reaction_posts'][str(post_id)]

        await ctx.message.add_reaction('✅')


    @remove.command(
        name='role',
        description='Удаляет роль по реакции',
        help='[id поста] [эмодзи]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def role(ctx, post_id, emoji):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')
        del server[str(ctx.guild.id)]['reaction_posts'][str(post_id)][str(emoji)]

        await ctx.message.add_reaction('✅')



def setup(bot):
    bot.add_cog(ReactionRole(bot))

