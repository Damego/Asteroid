import os
from random import randint, choice
from asyncio import sleep

import discord
from discord.ext import commands
from discord_components import *
import qrcode

from extensions.bot_settings import DurationConverter, get_embed_color, get_db, multiplier


server = get_db()



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

        member_roles = [
            role.mention for role in member.roles if role.name != "@everyone"
        ]

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
            **Дата регистрации в Discord:** <t:{int(member.created_at.timestamp())}:F>
            **Дата присоединения:** <t:{int(member.joined_at.timestamp())}:F>
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

    @commands.group(name='send',
        description='Отправляет сообщение в указанный канал',
        help='[канал] [сообщение]',
        invoke_without_command=True,
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def send_message(self, ctx, channel:discord.TextChannel, *, message):
        await channel.send(message)

    @send_message.command(name='delay',
        description='Отправляет отложенное сообщение в указанный канал',
        help='[канал] [время] [сообщение]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def delay_send_message(self, ctx, channel:discord.TextChannel, duration:DurationConverter, *, message):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])
        await channel.send(message)


    @commands.group(name='announce',
        description='Отправляет объявление в указанный канал',
        help='[канал] [сообщение]',
        invoke_without_command=True,
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def announce(self, ctx, channel:discord.TextChannel, *, message):
        embed = discord.Embed(title='Объявление!', description=message, color=get_embed_color(ctx.guild.id))
        await channel.send(embed=embed)


    @announce.command(name='delay',
        description='Отправляет объявление сообщение в указанный канал',
        help='[канал] [время] [сообщение]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def delay(self, ctx, channel:discord.TextChannel, duration:DurationConverter, *, message):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])

        embed = discord.Embed(title='Объявление!', description=message, color=get_embed_color(ctx.guild.id))
        await channel.send(embed=embed)


    @commands.command(name='serverinfo',
    aliases=['si', 'server', 'сервер'],
    description='Показывает информацию о текущем сервере',
    help='')
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f'Информация о сервере {guild.name}', color=get_embed_color(guild.id))
        embed.add_field(name='Дата создания:', value=f'<t:{int(guild.created_at.timestamp())}:F>', inline=False)
        embed.add_field(name='Основатель сервера:', value=guild.owner.mention, inline=False)

        embed.add_field(name='Количество', value=f"""
                                                :man_standing: **Участников:** {guild.member_count}
                                                :crown: **Ролей:** {len(guild.roles)}
                                                
                                                :hash: **Категорий:** {len(guild.categories)}
                                                :speech_balloon:** Текстовых каналов:** {len(guild.text_channels)}
                                                :speaker: **Голосовых каналов:** {len(guild.voice_channels)}
                                                """)
        embed.set_thumbnail(url=guild.icon_url)

        await ctx.send(embed=embed)
    


def setup(bot):
    bot.add_cog(Misc(bot))
