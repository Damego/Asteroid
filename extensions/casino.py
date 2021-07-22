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
                'last_free_chips':0,
            }
            await ctx.reply('Вы успешно зарегистрировались в Казино! Вам на счёт зачислено **1000** `фишек`!')
        else:
            await ctx.reply('Вы уже зарегистрированы в Казино')

    
    @commands.command(
        name='free',
        description='Выдаёт случаное количество фишек в пределах [100, 500]. Возможно использовать 1 раз в 12 часов',
        help='')
    async def free(self, ctx:commands.Context):
        try:
            user_casino = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]['casino']
        except KeyError:
            await ctx.reply('Вы не зарегистрированы в Казино! Зарегиструйтесь через команду `casino`')
            return
        last_free_chips = user_casino['last_free_chips']

        if int(time()) - last_free_chips < 43200:
            await ctx.reply('Вы можете получать фишки только раз в 12 часов!')
        else:
            chips = randint(100, 500)
            user_casino['chips'] += chips
            await ctx.reply(f'Вы получили `{chips}` фишек! Сейчас у вас `{user_casino["chips"]}` фишек. Следующая попытка будет доступна через 12 часов.')

    
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