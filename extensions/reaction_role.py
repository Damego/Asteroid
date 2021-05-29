from os import getenv

import discord
from discord.ext import commands
from replit import db, Database

if db is not None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = getenv('URL')
    server = Database(url)

def get_react_post_id(guild_id):
    """Get guild react post id from json """
    return server[str(guild_id)]['REACTION_POSTS']

def get_emoji_role(guild_id, message_id, emoji):
    """Get guild emoji roles from json """
    return server[str(guild_id)]['REACTION_POSTS'][str(message_id)][str(emoji)]


class ReactionRole(commands.Cog, description='Роль по реакции'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        posts = get_react_post_id(payload.guild_id)
        if str(payload.message_id) in posts:
            emoji = payload.emoji.id
            if payload.emoji.id == None:
                emoji = payload.emoji

            role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=get_emoji_role(payload.guild_id, payload.message_id, emoji))
            await payload.member.add_roles(role)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        posts = get_react_post_id(payload.guild_id)
        if str(payload.message_id) in posts:
            emoji = payload.emoji.id
            if payload.emoji.id == None:
                emoji = payload.emoji

            role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=get_emoji_role(payload.guild_id, payload.message_id, emoji))
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            await member.remove_roles(role)

    @commands.command(description='Записывает пост для выдачи роли по реакции', help='[id поста]')
    @commands.has_guild_permissions(administrator=True)
    async def add_react_post(self, ctx, post_id:int):
        server[str(ctx.guild.id)]['REACTION_POSTS'][str(post_id)] = {}

        embed = discord.Embed(title='Пост записан')
        await ctx.message.channel.purge(limit=1)
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(description='Удаляет пост для выдачи роли по реакции', help='[id поста]')
    @commands.has_guild_permissions(administrator=True)
    async def remove_react_post(self, ctx, post_id:int):
        del server[str(ctx.guild.id)]['REACTION_POSTS'][str(post_id)]

        embed = discord.Embed(title='Пост удалён')
        await ctx.message.channel.purge(limit=1)
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(description='Добавляет роль по реакции', help='[id поста] [эмодзи] [роль]')
    @commands.has_guild_permissions(administrator=True)
    async def add_react_role(self, ctx, post_id, emoji, role:discord.Role):
        """
        I don't know, why discord.PartialEmoji can't convert unicode emoji!
        discord.ext.commands.errors.PartialEmojiConversionFailure: Couldn't convert "😄" to PartialEmoji.
        """
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')
        server[str(ctx.guild.id)]['REACTION_POSTS'][str(post_id)][str(emoji)] = role.id

        embed = discord.Embed(title='Emoji записано!')
        await ctx.message.channel.purge(limit=1)
        await ctx.send(embed=embed, delete_after=5)


    @commands.command(description='Удаляет роль по реакции',help='[id поста] [эмодзи]')
    @commands.has_guild_permissions(administrator=True)
    async def remove_react_role(self, ctx, post_id, emoji):
        if emoji[0] == '<':
            emoji = emoji.split(':')[2].replace('>','')
        del server[str(ctx.guild.id)]['REACTION_POSTS'][str(post_id)][str(emoji)]

        embed = discord.Embed(title='Emoji удалено!')
        await ctx.message.channel.purge(limit=1)
        await ctx.send(embed=embed, delete_after=5)



def setup(bot):
    bot.add_cog(ReactionRole(bot))

