from asyncio import TimeoutError

import discord
from discord_components import Button, ButtonStyle
from discord.ext import commands

from .bot_settings import get_embed_color
from ._blackjack import BlackJack
from ._tictactoe import TicTacToe
from ._rockpaperscissors import RockPaperScissors



class Games(commands.Cog, description='Игры'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False


    @commands.command(aliases=['rps'], description='Запускает игру Камень-ножницы-бумага\nПервый ход получает тот, кого пригласили в игру', help='[ник] [кол-во игр]')
    async def rockpaperscissors(self, ctx:commands.Context, member: discord.Member, total_rounds: int = 1):
        if member == ctx.author:
            await ctx.send('Вы не можете пригласить себя!')
            return

        msg, accept = await self.invite_to_game(ctx, member, 'Камень-Ножницы-Бумага')

        if not accept:
            return

        game = RockPaperScissors(self.bot, ctx, member, msg, total_rounds)
        await game.start_game()


    @commands.command(aliases=['ttt'], description='Запускает игру Крестики-Нолики \nПервый ход получает тот, кого пригласили в игру', help='[ник]')
    async def tictactoe(self, ctx:commands.Context, member: discord.Member):
        if member == ctx.author:
            await ctx.send('Вы не можете пригласить себя!')
            return
        if member.bot:
            await ctx.send('Вы не можете пригласить бота!')
            return
        msg, accept = await self.invite_to_game(ctx, member, 'Крестики-Нолики')
        if not accept:
            return

        game = TicTacToe(self.bot, msg, ctx, member)
        await game.start_game()


    @commands.group(name='blackjack', description='Запускает игру Блэкджек', help='', invoke_without_command=True)
    async def blackjack(self, ctx:commands.Context):
        start_menu_components = [[
                Button(style=ButtonStyle.green, label='Начать игру', id='start_game'),
                Button(style=ButtonStyle.red, label='Выйти из игры', id='exit_game'),
            ]]

        msg = await ctx.send(content='Блэкджек', components=start_menu_components)

        interaction = await self.bot.wait_for('button_click', check=lambda i: i.user.id == ctx.author.id)
        await interaction.respond(type=6)

        if interaction.component.id == 'exit_game':
            await msg.delete()
            return
        blackjack = BlackJack(self.bot)
        await blackjack.prepare_for_game(ctx, msg)


    @blackjack.command(name='rules', description='Выводит правила Блэкджека', help='')
    async def rules(self, ctx:commands.Context):
        description = f"""
        **Правила игры в Блэкджек**
*Карты:*
    Всего карт: `52`. от 2 До Туза
    Номинальные значения карт следующее, от двойки до десятки совпадают с номиналом.
    Валет, Дама и Король имеют десять очков.
    Туз на данный момент имеет **только** 11 очков!
*Ход игры:*
    Дилер раздает игроку и себе по 2 карты, и при этом открывает свою одну карту, а вторая остаётся закрытой.
    Игрок может брать себе карту, до тех пор, пока не наступит 21 очко(Блэкджек), или перебор.
    Игрок может остановиться и передать ход дилеру.
*Выигрыш или проигрыш:*
    Если сумма карт Игрока `равна` 21, то это Блэкджек.
    Если сумма карт Игрока `больше` 21, то это перебор, и проигрыш.
    Если сумма карт Дилера `равна` 21, то это Блэкджек у Дилера.
    Если сумма карт Дилера `больше`, чем у Игрока, то побеждает Дилер.
    Если сумма карт Дилера `меньше`, чем у Игрока, то побеждает Игрок.
    Если сумма карт Дилера и Игрока `равны`, то это Ничья.

    За выигрыш вам даётся 100 очков опыта, а за Блэкджек, 200 очков
    
    """
        await ctx.send(description)


    async def invite_to_game(self, ctx, member, game_name):
        def member_agree(interaction):
            return interaction.user.id == member.id and interaction.channel.id == ctx.channel.id and interaction.message.id == msg.id

        msg = await ctx.send(
            content=f"{member.mention}! {ctx.author.name} приглашает тебя в игру {game_name}",
            components=[
                [
                    Button(style=ButtonStyle.green, label='Согласиться', id=1),
                    Button(style=ButtonStyle.red, label='Отказаться', id=2)
                ]])
        if member.bot:
            embed = discord.Embed(
                title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}', color=get_embed_color(ctx.guild.id))
            await msg.edit(context=' ', embed=embed)
            return msg, True
            
        try:
            interaction = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
            await interaction.respond(type=6)
        except TimeoutError:
            await msg.edit(content=f'От {member.display_name} нет ответа!', components=[])
            return msg, False

        if interaction.component.id == '1':
            embed = discord.Embed(
                title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}', color=get_embed_color(ctx.guild.id))
            await msg.edit(context=' ', embed=embed)
            return msg, True

        await msg.edit(content=f'{member.display_name} отказался от игры!', components=[])
        return msg, False


def setup(bot):
    bot.add_cog(Games(bot))
