import discord
from discord.ext import commands

from .bot_settings import get_db
from ._blackjack_online import BlackJackOnline


class Casino(commands.Cog, description='Казино'):
    def __init__(self, bot):
        self.bot = bot
        self.server = get_db()

    @commands.group(name='casino', description='Регистрирует вас в Казино', help='', invoke_without_command=True)
    async def casino(self, ctx:commands.Context):
        user = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
        if 'casino' not in user:
            user['casino'] = {
                'chips': 1000
            }
            await ctx.reply('Вы успешно зарегистрировались в Казино!')
        else:
            await ctx.reply('Вы уже зарегистрированы в Казино')

    
    @casino.command(name='blackjack', aliases=['bj'], description='Запускает Блэкджек онлайн', help='')
    async def blackjack(self, ctx:commands.Context):
        game = BlackJackOnline(self.bot)
        await game.init_game(ctx)

    @casino.command(name='add_chips', description='Добавляет фишки пользователю', help='[участник] [кол-во фишек]')
    async def add_chips(self, ctx:commands.Context, member:discord.Member, chips:int):
        try:
            self.server[str(ctx.guild.id)]['users'][str(member.id)]['casino']['chips'] += chips
        except KeyError:
            await ctx.reply('Пользователь не зарегистрирован в Казино!')
        else:
            await ctx.message.add_reaction('✅')

    @casino.command(name='about', description='', help='')
    async def about(self, ctx:commands.Context):
        content = f"""
        Было добавлено Казино и 1 игра, Блэкджек.
        Чтобы начать играть, вам необходимо зарегистрироваться в Казино через команду `casino`
        Вам на счёт будет выдано 1000 фишек. Вы можете их использовать в играх, делая ставки.
        """
        await ctx.send(content)



def setup(bot):
    bot.add_cog(Casino(bot))