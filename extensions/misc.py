import os
from random import randint, choice
from asyncio import sleep

import discord
from discord.ext import commands
import qrcode

from extensions.bot_settings import DurationConverter, get_embed_color, get_db, multiplier


server = get_db()

def get_stats(message, member):
    """Get guild members stats from json """
    ls = {
        'xp':server[str(message.guild.id)]['users'][str(member.id)]['xp'],
        'lvl':server[str(message.guild.id)]['users'][str(member.id)]['level']
        }
    return ls

def get_emoji_status(message):
    """Get guild emoji status for stats from json """
    ls = {
        'online':server[str(message.guild.id)]['emoji_status']['online'],
        'dnd':server[str(message.guild.id)]['emoji_status']['dnd'],
        'idle':server[str(message.guild.id)]['emoji_status']['idle'],
        'offline':server[str(message.guild.id)]['emoji_status']['offline'],
        }
    return ls



class Misc(commands.Cog, description='Остальные команды'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['misc', 'other']

    @commands.command(aliases=['рандом'], name='random', description='Выдаёт рандомное число в заданном промежутке', help='[от] [до]')
    async def random_num(self, ctx, arg1:int, arg2:int):
        num = randint(arg1,arg2)
        await ctx.reply(f'Рандомное число: {num}')

    @commands.command(name='coin', aliases=['орел', 'решка','монетка'], description='Кидает монетку, может выпасть орёл или решка', help=' ')
    async def coinflip(self, ctx):
        ls = ['Орёл', 'Решка']
        result = choice(ls)
        if result == 'Орёл':
            result = 'Вам выпал Орёл! <:eagle_coin:855061929827106818>'
        else:
            result = 'Вам выпала Решка! <:tail_coin:855060316609970216>'
        await ctx.reply(result)


    @commands.command(aliases=['инфо'], description='Выводит информацию об участнике канала', help='[ник]')
    async def info(self, ctx, member: discord.Member):
        try:
            user_level = server[str(ctx.guild.id)]['users'][str(member.id)]['level']
            user_xp = server[str(ctx.guild.id)]['users'][str(member.id)]['xp']
        except KeyError:
            user_level = 0
            user_xp = 0

        embed = discord.Embed(title=f'Информация о пользователе {member}', color=get_embed_color(ctx.guild.id))

        member_roles = []
        for role in member.roles:
            if role.name != "@everyone":
                member_roles.append(role.mention)
        member_roles = member_roles[::-1]
        member_roles = ', '.join(member_roles)
        

        member_status = str(member.status)
        status = {
            'online':'<:s_online:850792217031082051> В сети',
            'dnd':'<:dnd:850792216943525936> Не беспокоить',
            'idle':'<:s_afk:850792216732368937> Не активен',
            'offline':'<:s_offline:850792217262030969> Не в сети'
        }

        embed.add_field(name= "Основная информация:", value=f"""
            **Дата регистрации в Discord:** {member.created_at.strftime("%#d %B %Y")}
            **Дата присоединения на сервер:** {member.joined_at.strftime("%#d %B %Y")}
            **Текущий статус:** {status.get(member_status)}
            **Роли:** {member_roles}
            """, inline=False)

        embed.add_field(name='Уровень:', value=user_level)
        embed.add_field(name='Опыт:', value=f'{user_xp}/{user_level ** 4}')

        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(name='qr', aliases=['QR', 'код'], description='Создаёт QR-код', help='[текст]')
    async def create_qr(self, ctx, *, text):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1
        )
        qr.add_data(data=text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f'./qrcodes/{ctx.message.author.id}.png')
        await ctx.send(file = discord.File(f'./qrcodes/{ctx.message.author.id}.png'))
        os.remove(f'./qrcodes/{ctx.message.author.id}.png')

    @commands.command(description='Показывает пинг бота', help='')
    async def ping(self, ctx):
        embed = discord.Embed(title='🏓 Pong!', description=f'Задержка бота `{int(ctx.bot.latency * 1000)}` мс', color=get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)

    @commands.command(name='send', aliases=['an'], description='Отправляет сообщение в указанный канал', help='[канал] [сообщение]')
    @commands.has_guild_permissions(manage_messages=True)
    async def send_msg(self, ctx, channel:discord.TextChannel, *, message):
        await channel.send(message)

    @commands.command(name='delay_send', description='Отправляет отложенное сообщение', help='[канал] [время] [сообщение]')
    @commands.has_guild_permissions(manage_messages=True)
    async def delay_send_msg(self, ctx, channel:discord.TextChannel, duration:DurationConverter, *, message):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])
        await channel.send(message)

    @commands.command(name='serverinfo', aliases=['si', 'server', 'сервер'], description='Показывает информацию о текущем сервере', help='')
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f'Информация о сервере {guild.name}', color=get_embed_color(guild.id))
        embed.add_field(name='Дата создания:', value=guild.created_at, inline=False)
        embed.add_field(name='Основатель сервера:', value=guild.owner.mention, inline=False)
        embed.add_field(name='Количество ролей:', value=len(guild.roles), inline=False)
        embed.add_field(name='Количество участников:', value=guild.member_count, inline=False)
        embed.add_field(name='Количество каналов:', value=f"""
        :hash: Категорий: {len(guild.categories)}
        :writing_hand: Текстовых каналов: {len(guild.text_channels)}
        :speaker: Голосовых каналов: {len(guild.voice_channels)}
        """, inline=False)
        embed.set_thumbnail(url=guild.icon_url)

        await ctx.send(embed=embed)
    


def setup(bot):
    bot.add_cog(Misc(bot))
