from time import time
from random import randint

import discord
from discord.ext import commands

from .bot_settings import get_db
from ._blackjack_online import BlackJackOnline


class Casino(commands.Cog, description='Казино'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.server = get_db()

    @commands.group(name='casino', description='Регистрирует вас в Казино', help='', invoke_without_command=True)
    async def casino(self, ctx:commands.Context):
        user = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
        if 'casino' not in user:
            user['casino'] = {
                'chips': 1000,
                'free_chips_timeout':0,
            }
            await ctx.reply('Вы успешно зарегистрировались в Казино! Вам на счёт зачислено **1000** `фишек`!')
        else:
            await ctx.reply('Вы уже зарегистрированы в Казино')

    @casino.command(name='clear', description='Обнуляет пользователя в Казино', help='[участник]')
    @commands.has_guild_permissions(administrator=True)
    async def clear(self, ctx:commands.Context, member:discord.Member):
        user = self.server[str(ctx.guild.id)]['users'][str(member.id)]
        if 'casino' not in user:
            await ctx.reply('Пользователь не зарегистрирован в Казино!')
            return
        user['casino'] = {
            'chips': 1000,
            'free_chips_timeout':0,
        }
        await ctx.message.add_reaction('✅')


    @casino.command(
        name='free',
        description='Выдаёт случаное количество фишек в пределах [100, 500]. Возможно использовать 1 раз в 12 часов',
        help='')
    async def free(self, ctx:commands.Context):
        try:
            user_casino = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]['casino']
        except KeyError:
            await ctx.reply('Вы не зарегистрированы в Казино! Зарегиструйтесь через команду `casino`')
            return
        free_chips_timeout = user_casino['free_chips_timeout']
        timeout = user_casino['free_chips_timeout'] + 43200
        

        if int(time()) - free_chips_timeout < 43200:
            await ctx.reply('Следующая попытка будет доступна <t:{timeout}:R>.')
        else:
            chips = randint(100, 500)
            user_casino['chips'] += chips
            user_casino['free_chips_timeout'] = int(time())

            await ctx.reply(f"""
            Вы получили `{chips}` фишек! Сейчас у вас `{user_casino["chips"]}` фишек.
            Следующая попытка будет доступна <t:{timeout}:R>.""")

    
    @casino.command(name='blackjack', aliases=['bj'], description='Запускает Блэкджек онлайн', help='')
    async def blackjack(self, ctx:commands.Context):
        game = BlackJackOnline(self.bot)
        await game.init_game(ctx)


    @casino.command(name='add_chips', description='Добавляет фишки пользователю', help='[участник] [кол-во фишек]')
    @commands.has_guild_permissions(administrator=True)
    async def add_chips(self, ctx:commands.Context, member:discord.Member, chips:int):
        try:
            self.server[str(ctx.guild.id)]['users'][str(member.id)]['casino']['chips'] += chips
        except KeyError:
            await ctx.reply('Пользователь не зарегистрирован в Казино!')
        else:
            await ctx.message.add_reaction('✅')

    @casino.command(name='about', description='Выдаёт небольшую информацию о Казино', help='')
    async def about(self, ctx:commands.Context):
        content = """
        Было добавлено Казино и 1 игра, Блэкджек.
        Чтобы начать играть, вам необходимо зарегистрироваться в Казино через команду `casino`
        Вам на счёт будет выдано 1000 фишек. Вы можете их использовать в играх, делая ставки.
        """
        await ctx.send(content)



def setup(bot):
    bot.add_cog(Casino(bot))