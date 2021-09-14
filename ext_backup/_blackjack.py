from random import choice

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle



class BlackJack():
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

        self.spades = {'♠2', '♠3', '♠4', '♠5', '♠6', '♠7', '♠8', '♠9', '♠10', '♠В', '♠Д', '♠К', '♠Т'}
        self.clubs = {'♣2', '♣3', '♣4', '♣5', '♣6', '♣7', '♣8', '♣9', '♣10', '♣В', '♣Д', '♣К', '♣Т'}
        self.hearts = {'♥2', '♥3', '♥4', '♥5', '♥6', '♥7', '♥8', '♥9', '♥10', '♥В', '♥Д', '♥К', '♥Т'}
        self.diamonds = {'♦2', '♦3', '♦4', '♦5', '♦6', '♦7', '♦8', '♦9', '♦10', '♦В', '♦Д', '♦К', '♦Т'}


    async def prepare_for_game(self, ctx:commands.Context, message:discord.Message):
        self.guild_id = ctx.guild.id
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
            if taking_card_loop == 0:
                self.hidden_sum_diler_cards += self.all_nums[card[1:]]
                self.hidden_card_list.append(card)
                self.hidden_card_list.append('?')

        embed = self.update_embed(False)

        menu_components = [[
            Button(style=ButtonStyle.blue,
                    label='Take', id='take_card'),
            Button(style=ButtonStyle.blue,
                    label='Hold', id='hold'),
            Button(style=ButtonStyle.red,
                    label='Exit', id='exit_from_game'),
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
                await message.edit(content='You leave game!', components=[])
                return


    def update_embed(self, diler_move:bool):
        if not diler_move:
            diler_cards_str = ', '.join(self.hidden_card_list)
            sum_diler_cards = self.hidden_sum_diler_cards
            
        if diler_move:
            diler_cards_str = ', '.join(self.diler_cards_list)
            sum_diler_cards = self.sum_diler_cards

        user_cards_str = ', '.join(self.user_cards_list)
        embed = discord.Embed(title='Blackjack', color=self.bot.get_embed_color(self.guild_id))
        embed.add_field(name='Diler\'s cards:', value=f'```{diler_cards_str}```\n**Cards sum:** `{sum_diler_cards}`')
        embed.add_field(name='Yours cards:', value=f'```{user_cards_str}```\n**Cards sum:** `{self.sum_user_cards}`')
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
                await ctx.send('Blackjack! You win!')
                return True
            elif self.sum_user_cards > 21:
                await ctx.send('Too many cards. You lose!')
                return True

        if diler_move:
            if self.sum_diler_cards == 21:
                await ctx.send('Diler\'s BlackJack! You lose!')
                return True
            elif self.sum_diler_cards > 21:
                await ctx.send('Diler have too many cards! You win!')
                return True
            elif self.sum_user_cards == self.sum_diler_cards:
                await ctx.send('Draw!')
                return True
            elif self.sum_diler_cards > self.sum_user_cards:
                await ctx.send('You lose!')
                return True
            elif self.sum_diler_cards < self.sum_user_cards:
                await ctx.send('You win!')
                return True
        return False