import os
import asyncio

import discord
from discord.ext import commands
from replit import Database, db


if db != None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)

def get_embed_color(message):
    """Get color for embeds from json """
    """with open('jsons/servers.json', 'r') as f:
        server = json.load(f)"""

    return int(server[str(message.guild.id)]['embed_color'], 16)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_ls = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            msg = message.content
            if message.author.id not in self.spam_ls:
                print(f'[SPAM_FILTER] {message.author} wrote message: "{message.content}"')
                self.spam_ls[message.author.id] = {}
                self.spam_ls[message.author.id]['msg'] = msg
                self.spam_ls[message.author.id]['count'] = 1

            elif msg == self.spam_ls[message.author.id]['msg']:
                print(f'[SPAM_FILTER] {message.author} wrote same message: "{message.content}"')
                self.spam_ls[message.author.id]['count'] += 1

            elif msg != self.spam_ls[message.author.id]['msg']:
                print(f'[SPAM_FILTER] {message.author} wrote new message: "{message.content}"')
                self.spam_ls[message.author.id]['count'] = 1
                self.spam_ls[message.author.id]['msg'] = msg

            if self.spam_ls[message.author.id]['count'] > 2:
                count = self.spam_ls[message.author.id]['count']
                self.spam_ls[message.author.id]['count'] = 0

                print(f'[SPAM_FILTER] Removing messages of {message.author}')
                await message.channel.purge(limit=count)
                await message.channel.send(f'**{message.author.mention}, Ваши сообщения были удалены из-за спама!**')


    @commands.command(aliases=['мут'], description='Даёт мут участнику на время')
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx, member:discord.Member, time:int,* ,reason=None):
        await member.edit(mute=True)
        embed = discord.Embed(title=f'{member} был отправлен в мут!', color=get_embed_color(ctx.message))
        embed.add_field(name='Причина:', value=f'{reason}',inline=False)
        embed.add_field(name='Время:',value=f'{time // 60} мин. {time % 60} сек.')
        await ctx.send(embed=embed)
        await asyncio.sleep(time)
        try:
            await self.unmute(ctx, member)
        except Exception:
            print('[Moderation] unmute USER NOT FOUND')

    @commands.command(aliases=['дизмут', 'анмут'], description='Снимает мут с участника')
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx, member:discord.Member):
        await member.edit(mute=False)
        embed = discord.Embed(title=f'Мут с {member} снят!', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)

    @commands.has_guild_permissions(ban_members=True)
    @commands.command(aliases=['бан'], description='Банит участника сервера')
    async def ban(self, ctx, member:discord.Member, *, reason=None):
        await member.ban(reason=reason)
        embed = discord.Embed(title=f'{member} был заблокирован!',description=f'Причина: {reason}', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)


    @commands.command(aliases=['анбан', 'дизбан'], description='Снимает бан у участника')
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, member):
        banned_users = await ctx.guild.bans()
        member_name, member_disc = member.split('#')

        for ban in banned_users:
            user = ban.user
            if (user.name, user.discriminator) == (member_name, member_disc):
                await ctx.guild.unban(user)
                embed = discord.Embed(title=f'С пользователя {member} снята блокировка!', color=get_embed_color(ctx.message))
                return await ctx.send(embed=embed)
                    

    @commands.command(aliases=['кик'], description='Кикает участника с сервера')
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason=None):
        await member.kick(reason=reason)
        embed = discord.Embed(title=f'{member} был кикнут с сервера!',description=f'Причина: {reason}', color=get_embed_color(ctx.message))
        await ctx.send(embed=embed)


    @mute.error
    @unmute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title=f'Пользователь не подключен к голосовому каналу! {error}', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed)



    @commands.command(aliases=['роль-'], description='Удаляет роль с участника')
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role): # Убирает роль с участника
        """Remove role from member"""
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = get_embed_color(ctx.message)) 
        await ctx.send(embed=embed)

    @commands.command(aliases=['роль+'], description='Добавляет роль участнику')
    @commands.has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, role: discord.Role, time=None): # Выдаёт роль участнику
        await member.add_roles(role)
        if time != None:
            desc = f'Роль {role} была добавлена! \n Время: {time} сек.'
        else:
            desc = f'Роль {role} была добавлена!'
        embed = discord.Embed(title=f'{member}', description=desc,color = get_embed_color(ctx.message))
        await ctx.send(embed=embed)

        if time != None:
            await asyncio.sleep(int(time))
            await self.remove_role(ctx, member, role)

    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.command(aliases=['ник'], description='Меняет ник участнику')
    async def nick(self, ctx, member:discord.Member, newnick):
        oldnick = member
        await member.edit(nick=newnick)
        await ctx.send(f'{oldnick.mention} стал {newnick}')


    @commands.command(aliases=['очистить', 'очистка', 'чистить',"чист"], description='Очищает сообщения', help='clear [КОЛВО]')
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx, amount:int):
        await ctx.channel.purge(limit=amount+1)


def setup(bot):
    bot.add_cog(Moderation(bot))