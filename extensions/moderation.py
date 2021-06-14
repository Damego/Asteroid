import asyncio

import discord
from discord.ext import commands

from extensions.bot_settings import get_embed_color, get_db

server = get_db()

def get_prefixs(message): 
    """Get guild prexif from json """
    return server[str(message.guild.id)]['prefix']


class Moderation(commands.Cog, description='Модерация'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.spam_ls = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            msg = message.content
            if msg[0] != get_prefixs(message):
                if message.author.id not in self.spam_ls or msg != self.spam_ls[message.guild.id][message.channel.id][message.author.id]['message_content']:
                    print(f'[SPAM_FILTER] {message.author} wrote message: "{message.content}"')
                    self.spam_ls[message.guild.id] = {}
                    self.spam_ls[message.guild.id][message.channel.id] = {}
                    self.spam_ls[message.guild.id][message.channel.id][message.author.id] = {}
                    self.spam_ls[message.guild.id][message.channel.id][message.author.id]['message_content'] = msg
                    self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] = 1

                elif msg == self.spam_ls[message.guild.id][message.channel.id][message.author.id]['message_content']:
                    print(f'[SPAM_FILTER] {message.author} wrote same message')
                    self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] += 1

                if self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] > 2:
                    count = self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count']
                    self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] = 0

                    print(f'[SPAM_FILTER] Removing messages of {message.author}')
                    await message.channel.purge(limit=count)
                    await message.channel.send(content=f'**{message.author.mention}, Ваши сообщения были удалены из-за спама!**', delete_after=10)

    @commands.command(description='Даёт мут участнику на время', help='[ник] [время(сек)] [причина]')
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx, member:discord.Member, time:int,* ,reason=None):
        await ctx.message.add_reaction('✅')
        await member.edit(mute=True)
        embed = discord.Embed(title=f'{member} был отправлен в мут!', color=get_embed_color(ctx.message))
        embed.add_field(name='Причина:', value=f'{reason}',inline=False)
        embed.add_field(name='Время:',value=f'{time // 60} мин. {time % 60} сек.')
        await ctx.send(embed=embed)
        await asyncio.sleep(time)
        try:
            await self.unmute(ctx, member)
        except Exception:
            print('[Moderation] Member not found for unmuting')

    @commands.command(description='Снимает мут с участника', help='[ник]')
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx, member:discord.Member):
        await member.edit(mute=False)
        embed = discord.Embed(title=f'Мут с {member} снят!', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)

    @commands.has_guild_permissions(ban_members=True)
    @commands.command(description='Банит участника сервера', help='[ник] [причина]')
    async def ban(self, ctx, member:discord.Member, *, reason=None):
        await member.ban(reason=reason)
        embed = discord.Embed(title=f'{member} был заблокирован!',description=f'Причина: {reason}', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)

    @commands.command(description='Снимает бан у участника', help='[ник]')
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, member:discord.Member):
        await member.unban()
        embed = discord.Embed(title=f'С пользователя {member} снята блокировка!', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)
                    
    @commands.command(description='Кикает участника с сервера', help='[ник] [причина]')
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason=None):
        await member.kick(reason=reason)
        embed = discord.Embed(title=f'{member} был кикнут с сервера!',description=f'Причина: {reason}', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)

    @commands.command(aliases=['роль-'], description='Удаляет роль с участника', help='[ник] [роль]')
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
        """Remove role from member"""
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = get_embed_color(ctx.message)) 
        await ctx.send(embed=embed)

    @commands.command(aliases=['роль+'], description='Добавляет роль участнику', help='[ник] [роль]')
    @commands.has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        desc = f'Роль {role} была добавлена!'
        embed = discord.Embed(title=f'{member}', description=desc,color = get_embed_color(ctx.message))
        await ctx.send(embed=embed)


    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.command(aliases=['ник'], description='Меняет ник участнику', help='[ник] [новый ник]')
    async def nick(self, ctx, member:discord.Member, newnick):
        oldnick = member
        await member.edit(nick=newnick)
        await ctx.send(f'{oldnick.mention} стал {newnick}')

    @commands.command(description='Очищает сообщения', help='[Кол-во сообщений]')
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx, amount:int):
        await ctx.channel.purge(limit=amount+1)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title=f'Пользователь не подключен к голосовому каналу!', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))