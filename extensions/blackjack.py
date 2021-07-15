from random import choice

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle

from .bot_settings import get_embed_color
from ._levels import update_member



class BlackJack(commands.Cog, description='Блэкджек'):
    def __init__(self, bot):
        self.bot = bot
        self.all_nums = {
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
            '6': 6,
            '7': 7,
            '8': 8,
            '9': 9,
            '10': 10,
            'В': 10,
            'Д': 10,
            'К': 10,
            'Т': 11,
        }
        self.hidden = False

        self.spades = {'♠2', '♠3', '♠4', '♠5', '♠6', '♠7', '♠8', '♠9', '♠10', '♠В', '♠Д', '♠К', '♠Т'}
        self.clubs = {'♣2', '♣3', '♣4', '♣5', '♣6', '♣7', '♣8', '♣9', '♣10', '♣В', '♣Д', '♣К', '♣Т'}
        self.hearts = {'♥2', '♥3', '♥4', '♥5', '♥6', '♥7', '♥8', '♥9', '♥10', '♥В', '♥Д', '♥К', '♥Т'}
        self.diamonds = {'♦2', '♦3', '♦4', '♦5', '♦6', '♦7', '♦8', '♦9', '♦10', '♦В', '♦Д', '♦К', '♦Т'}


    @commands.group(name='blackjack', description='Запускает игру Блэкджек', help='', invoke_without_command=True)
    async def blackjack(self, ctx:commands.Context):
        self.guild_id = ctx.guild.id
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
        await self.prepare_for_game(ctx, msg)

        
    async def prepare_for_game(self, ctx:commands.Context, message:discord.Message):
        self.sum_user_cards = 0
        self.sum_diler_cards = 0
        self.hidden_sum_diler_cards = 0
        self.hidden_card_list = []
        self.diler_cards_list = []
        self.user_cards_list = []

        self.available_cards = list(self.spades) + list(self.clubs) + list(self.hearts) + list(self.diamonds)

        for taking_card_loop in range(2):
            self.user_take_card()
            card = self.diler_take_card()
            if taking_card_loop < 1:
                self.hidden_sum_diler_cards += self.all_nums[card[1:]]
                self.hidden_card_list.append(card)
                self.hidden_card_list.append('?')

        embed = self.update_embed(False)

        menu_components = [[
            Button(style=ButtonStyle.blue,
                    label='Взять карту', id='take_card'),
            Button(style=ButtonStyle.blue,
                    label='Передать ход', id='hold'),
            Button(style=ButtonStyle.red,
                    label='Выйти из игры', id='exit_from_game'),
        ]]
        await message.edit(embed=embed, components=menu_components)

        end = await self.is_end(ctx)
        if end:
            await message.edit(components=[])
            return

        await self.start_game(ctx, message)

    async def start_game(self, ctx:commands.Context, message:discord.Message):
        while True:
            interaction = await self.bot.wait_for('button_click', check=lambda i: i.user.id == ctx.author.id)
            await interaction.respond(type=6)

            i_value = interaction.component.id
            if i_value == 'take_card':
                self.user_take_card()

                embed = self.update_embed(False)
                await message.edit(embed=embed)

                end = await self.is_end(ctx)
                if end:
                    embed = self.update_embed(True)
                    await message.edit(embed=embed, components=[])
                    return

            elif i_value == 'hold':
                while True:
                    if self.sum_diler_cards < 17:
                        self.diler_take_card()
                        embed = self.update_embed(True)
                        await message.edit(embed=embed)
                    elif self.sum_diler_cards > 16:
                        embed = self.update_embed(True)
                        await message.edit(embed=embed)
                        end = await self.is_end(ctx, True)
                        if end:
                            await message.edit(components=[])
                            return
            elif i_value == 'exit_from_game':
                return


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


 # * METHODS
    def update_embed(self, diler_move:bool):
        if not diler_move:
            diler_cards_str = ', '.join(self.hidden_card_list)
            sum_diler_cards = self.hidden_sum_diler_cards
            
        if diler_move:
            diler_cards_str = ', '.join(self.diler_cards_list)
            sum_diler_cards = self.sum_diler_cards

        user_cards_str = ', '.join(self.user_cards_list)
        embed = discord.Embed(title='Блэкджек', color=get_embed_color(self.guild_id))
        embed.add_field(name='Карты дилера:', value=f'```{diler_cards_str}```\n**Сумма карт:** `{sum_diler_cards}`')
        embed.add_field(name='Ваши карты:', value=f'```{user_cards_str}```\n**Сумма карт:** `{self.sum_user_cards}`')
        return embed


    def user_take_card(self):
        card = choice(self.available_cards)
        self.available_cards.remove(card)
        self.user_cards_list.append(card)
        self.sum_user_cards += self.all_nums[card[1:]]
        return card

    def diler_take_card(self):
        card = choice(self.available_cards)
        self.available_cards.remove(card)
        self.diler_cards_list.append(card)
        self.sum_diler_cards += self.all_nums[card[1:]]
        return card


    async def is_end(self, ctx:commands.Context, diler_move=False):
        if not diler_move:
            if self.sum_user_cards == 21:
                await ctx.send('У вас 21! Вы выиграли!')
                await update_member(ctx.author, 200)
                return True
            elif self.sum_user_cards > 21:
                await ctx.send('У вас перебор! Вы проиграли')
                return True

        if diler_move:
            if self.sum_diler_cards == 21:
                await ctx.send('у Дилера 21 очко! Вы проиграли!')
                return True
            elif self.sum_diler_cards > 21:
                await ctx.send('У Дилера перебор! Вы выиграли!')
                await update_member(ctx.author, 100)
                return True
            elif self.sum_user_cards == self.sum_diler_cards:
                await ctx.send('Ничья!')
                return True
            elif self.sum_diler_cards > self.sum_user_cards:
                await ctx.send('Вы проиграли! Сумма ваших карт меньше, чем у Дилера!')
                return True
            elif self.sum_diler_cards < self.sum_user_cards:
                await ctx.send('Вы выиграли! Сумма ваших карт больше, чем у Дилера!')
                await update_member(ctx.author, 100)
                return True
        return False



def setup(bot):
    bot.add_cog(BlackJack(bot))