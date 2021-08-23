from os import remove
from random import randint
from asyncio import sleep

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, Select, SelectOption
import qrcode

from .bot_settings import (
    DurationConverter,
    multiplier,
    version,
    is_administrator_or_bot_owner,
    )
from .levels._levels import formula_of_experience
#from ._hltv import HLTV


class Misc(commands.Cog, description='Остальные команды'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False



    @commands.command(aliases=['рандом'], name='random', description='Выдаёт рандомное число в заданном промежутке', help='[от] [до]')
    async def random_num(self, ctx, arg1:int, arg2:int):
        random_number = randint(arg1, arg2)
        await ctx.reply(f'Рандомное число: {random_number}')

    @commands.command(name='coin', aliases=['орел', 'решка','монетка'], description='Кидает монетку, может выпасть орёл или решка', help=' ')
    async def coinflip(self, ctx):
        result = randint(0,1)
        if result:
            content = 'Вам выпал Орёл! <:eagle_coin:855061929827106818>'
        else:
            content = 'Вам выпала Решка! <:tail_coin:855060316609970216>'

        await ctx.reply(content)


    @commands.group(
        name='info',
        aliases=['инфо'],
        description='Выводит информацию об участнике сервера',
        help='[ник]',
        invoke_without_command=True)
    async def info(self, ctx:commands.Context, member:discord.Member=None):
        if not member:
            member = ctx.author

        embed = discord.Embed(title=f'Информация о пользователе {member}', color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_thumbnail(url=member.avatar_url)

        member_roles = [role.mention for role in member.roles if role.name != "@everyone"][::-1]

        member_roles = ', '.join(member_roles)

        member_status = str(member.status)
        status = {
            'online':'<:s_online:850792217031082051> В сети',
            'dnd':'<:dnd:850792216943525936> Не беспокоить',
            'idle':'<:s_afk:850792216732368937> Не активен',
            'offline':'<:s_offline:850792217262030969> Не в сети'
        }

        embed.add_field(name="Основная информация:", value=f"""
            **Дата регистрации в Discord:** <t:{int(member.created_at.timestamp())}:F>
            **Дата присоединения:** <t:{int(member.joined_at.timestamp())}:F>
            **Текущий статус:** {status.get(member_status)}
            **Роли:** {member_roles}
            """, inline=False)

        if member.bot:
            return await ctx.send(embed=embed)

        stats = ''

        guild_users_collection = self.bot.get_guild_users_collection(ctx.guild.id)
        user = guild_users_collection.find_one({'_id':str(member.id)})

        user_voice_time = user.get('voice_time_count')
        user_leveling = user.get('leveling')
        user_casino = user.get('casino')

        if user_voice_time is not None:
            stats += f'<:voice_time:863674908969926656> **Время в голосом канале:** `{user_voice_time}` мин.'

        if user_leveling:
            user_level = user_leveling['level']
            xp_to_next_level = formula_of_experience(user_level)
            user_xp = user_leveling['xp']
            user_xp_amount =  user_leveling['xp_amount']
            
            stats += f"""
            <:level:863677232239869964> **Уровень:** `{user_level}`
            <:exp:863672576941490176> **Опыт:** `{user_xp}/{xp_to_next_level}` Всего: `{user_xp_amount}`
            """

        if user_casino:
            stats += f'\n <:casino_chips:867817313528971295>  **Фишек:** `{user_casino["chips"]}`'

        if stats:
            embed.add_field(name='Статистика:', value=stats)

        await ctx.send(embed=embed)


    @info.command(name='server',
    aliases=['s', 'сервер'],
    description='Показывает информацию о текущем сервере',
    help='')
    async def server_info(self, ctx:commands.Context):
        guild = ctx.guild
        embed = discord.Embed(title=f'Информация о сервере {guild.name}', color=self.bot.get_embed_color(guild.id))
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

    @info.command(name='bot', description='Показывает информацию о Боте', help='')
    async def info_bot(self, ctx:commands.Context):
        prefix = self.bot.get_guild_prefix(ctx.guild.id)
        embed = discord.Embed(title='Информация о боте', color=self.bot.self.bot.get_embed_color(ctx.guild.id))

        components= [
            Button(style=ButtonStyle.URL, label='Пригласить', url='https://discord.com/api/oauth2/authorize?client_id=828262275206873108&permissions=0&scope=bot')
        ]

        users_amount = sum(len(guild.members) for guild in self.bot.guilds)

        embed.description = f"""
                            **Создатель:** **Damego#0001**
                            **Текущая версия:** `{version}`
                            **Количество серверов:** `{len(ctx.bot.guilds)}`
                            **Количество пользователей:** `{users_amount}`
                            **Количество команд:** `{len(ctx.bot.commands)}`
                            **Текущий пинг:** `{int(ctx.bot.latency * 1000)}` мс
                            **Префикс на сервере:** `{prefix}`
                            """

        await ctx.send(embed=embed, components=components)


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
        remove(f'./qrcodes/{ctx.message.author.id}.png')


    @commands.command(description='Показывает пинг бота', help='')
    async def ping(self, ctx):
        embed = discord.Embed(title='🏓 Pong!', description=f'Задержка бота `{int(ctx.bot.latency * 1000)}` мс', color=self.bot.get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @commands.group(name='send',
        description='Отправляет сообщение в указанный канал',
        help='[канал] [сообщение]',
        invoke_without_command=True,
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def send_message(self, ctx, channel:discord.TextChannel, *, message):
        await channel.send(message)

    @send_message.command(name='delay',
        description='Отправляет отложенное сообщение в указанный канал',
        help='[канал] [время] [сообщение]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def delay_send_message(self, ctx, channel:discord.TextChannel, duration:DurationConverter, *, message):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])
        await channel.send(message)


    @commands.group(name='announce',
        description='Отправляет объявление в указанный канал',
        help='[канал] [сообщение]',
        invoke_without_command=True,
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def announce(self, ctx, channel:discord.TextChannel, *, message):
        embed = discord.Embed(title='Объявление!', description=message, color=self.bot.get_embed_color(ctx.guild.id))
        await channel.send(embed=embed)


    @announce.command(name='delay',
        description='Отправляет объявление сообщение в указанный канал',
        help='[канал] [время] [сообщение]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def delay(self, ctx, channel:discord.TextChannel, duration:DurationConverter, *, message):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])

        embed = discord.Embed(title='Объявление!', description=message, color=self.bot.get_embed_color(ctx.guild.id))
        await channel.send(embed=embed)


    @commands.command(name='hltv', description='Выводит дату ближайщих игр указанной комадны', help='[команда]')
    async def hltv(self, ctx:commands.Context, *, team):
        await HLTV.parse_mathes(ctx, team)


def setup(bot):
    bot.add_cog(Misc(bot))
