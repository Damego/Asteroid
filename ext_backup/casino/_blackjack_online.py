from random import choice

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, Interaction, Select, SelectOption

from ..bot_settings import get_embed_color, get_db



class BlackJackOnline:
    def __init__(self, bot):
        self.bot = bot
        self.server = get_db()

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


    async def init_game(self, ctx:commands.Context):
        self.players = [ctx.author.id]
        self.guild_id = ctx.guild.id

        embed = discord.Embed(title=f'Блэкджек. {1}/{7}', color=get_embed_color(self.guild_id))
        embed.description = f'**Участники:**\n{ctx.author.display_name} (Создатель)'
        components = [[
            Button(style=ButtonStyle.green, label='Присоединиться', id='join'),
            Button(style=ButtonStyle.blue, label='Начать игру', id='start_game'),
            Button(style=ButtonStyle.red, label='Удалить лобби', id='exit')
        ]]

        self.message:discord.Message = await ctx.send(embed=embed, components=components)

        while True:
            try:
                interaction:Interaction = await self.bot.wait_for('button_click')
            except Exception:
                continue

            value = interaction.component.id
            user_id = interaction.user.id

            if value == 'join':
                if 'casino' not in self.server[str(self.guild_id)]['users'][str(user_id)]:
                    await interaction.respond(content='Вы не зарегистрированы в Казино! Зарегистрируйтесь через команду `casino`')
                    continue

                if user_id in self.players:
                    await interaction.respond(content='Вы уже в лобби!')
                elif len(self.players) > 6:
                    await interaction.respond(type=4, content='Достигнуто максимальное количество участников!')
                else:
                    self.players.append(user_id)
                    embed.title = f'Блэкджек. {len(self.players)}/{7}'
                    embed.description += f'\n {interaction.user.display_name}'
                    await interaction.respond(type=7, embed=embed)
                    
            elif value == 'start_game':
                if user_id == ctx.author.id:
                    await interaction.respond(type=6)
                    await self.start_game(ctx)
                else:
                    await interaction.respond(content='Только Создатель лобби может начать игру!')

            elif value == 'exit':
                if user_id == ctx.author.id:
                    await self.message.delete()
                    return


    async def start_game(self, ctx:commands.Context):
        self.current_players = {}

        self.sum_diler_cards = 0
        self.diler_cards_list = []
        self.hidden_sum_diler_cards = 0
        self.hidden_card_list = []

        self.available_cards = list(self.spades) + list(self.clubs) + list(self.hearts) + list(self.diamonds)

        for player in self.players:
            member = await ctx.guild.fetch_member(player)
            self.current_players[str(player)] = {
                'nickname': member.display_name,
                'bet': 'Нет ставки',
                'cards': [],
                'sum_cards': 0,
                'end': False,
                'game_status': 'Играет'
            }

        await self.wait_bet()

        for loop in range(2):
            for player in self.current_players:
                self.player_take_card(player)
            card = self.diler_take_card()
            if loop == 0:
                self.hidden_sum_diler_cards += self.all_nums[card[1:]]
                self.hidden_card_list.append(card)
                self.hidden_card_list.append('?')
            else:
                self.endgame_for_player(player)

        await self.update_message()

        await self.players_move()
        await self.diler_move()
        await self.out_score(ctx)
    

    async def diler_move(self):
        while True:
            if self.sum_diler_cards < 17:
                self.diler_take_card()
                await self.update_message(True, True)
            elif self.sum_diler_cards > 16:
                await self.update_message(True, True)
                return
                

    async def players_move(self):
        components = [[
            Button(style=ButtonStyle.blue, label='Пас', id='stand'),
            Button(style=ButtonStyle.blue, label='Взять карту', id='take_card'),
            Button(style=ButtonStyle.blue, label='Дабл', id='double')
        ]]

        await self.message.edit(components=components)

        while True:
            try:
                interaction:Interaction = await self.bot.wait_for('button_click')
            except Exception:
                continue
            user_id = interaction.user.id

            if str(user_id) not in self.current_players:
                continue

            value = interaction.component.id
            user_stats = self.current_players[str(user_id)]

            if user_stats['end']:
                await interaction.respond(content='Вы больше не участвуете в игре!')
                continue

            if value == 'stand':
                user_stats['end'] = True
                user_stats['game_status'] = "Пас"
            if value == 'take_card':
                self.player_take_card(user_id)
            elif value == 'double':
                user_chips = self.server[str(self.guild_id)]['users'][str(user_id)]['casino']['chips']
                if user_chips < user_stats['bet'] * 2:
                    await interaction.respond(content='Недостаточно фишек!')
                else:
                    self.player_take_card(user_id)
                    user_stats['bet'] *= 2
            
            if not interaction.responded:
                await interaction.respond(type=6)

            await self.update_message()

            self.endgame_for_player(user_id)

            for player in self.current_players:
                if not self.current_players[player]['end']:
                    break
            else:
                return


    def endgame_for_player(self, user_id):
        sum_cards = self.current_players[str(user_id)]['sum_cards']
        cards = self.current_players[str(user_id)]['cards']

        if sum_cards == 21 or (sum_cards == 22 and len(cards) == 2):
            self.current_players[str(user_id)]['end'] = True
            self.current_players[str(user_id)]['game_status'] = 'Блэкджек'
        elif sum_cards > 21:
            self.current_players[str(user_id)]['end'] = True
            self.current_players[str(user_id)]['game_status'] = 'Перебор'


    async def update_message(self, diler_move=False, remove_buttons=False):
        if diler_move:
            cards = ', '.join(self.diler_cards_list)
            sum_cards = self.sum_diler_cards
        if not diler_move:
            cards = ', '.join(self.hidden_card_list)
            sum_cards = self.hidden_sum_diler_cards

        embed = discord.Embed(title='Блэкджек', color=get_embed_color(self.guild_id))
        embed.description = f'Участники:'
        embed.add_field(name='Дилер', value=f"""
        \u200b
        **Карты:** ```{cards}```
        **Сумма:** `{sum_cards}`
        """)

        for _player in self.current_players:
            player = self.current_players[_player]
            embed.add_field(name=player['nickname'], value=f"""
            **Ставка:** {player['bet']} фишек
            **Карты:** ```{', '.join(player['cards'])}```
            **Сумма:** `{player['sum_cards']}`
            **Статус:** {player['game_status']}""")

        if remove_buttons:
            await self.message.edit(embed=embed, components=[])
        else:
            await self.message.edit(embed=embed)


    async def update_bet_menu(self):
        embed = discord.Embed(title='Блэкджек. Введите ставку!', color=get_embed_color(self.guild_id))
        embed.description = '**Участники** | **Ставка**'

        for _player in self.current_players:
            player = self.current_players[_player]
            embed.description += f'\n{player["nickname"]} | {player["bet"]} `фишек`'

        components = [
            Select(
                placeholder='Выберите количество фишек для ставки!',
                options=[
                    SelectOption(label='Без ставки', value=0),
                    SelectOption(label='10 фишек', value=10),
                    SelectOption(label='50 фишек', value=50),
                    SelectOption(label='100 фишек', value=100),
                    SelectOption(label='150 фишек', value=150),
                    SelectOption(label='200 фишек', value=200),
                    SelectOption(label='500 фишек', value=500),
                    SelectOption(label='1000 фишек', value=1000),
                ]
            )
        ]

        await self.message.edit(embed=embed, components=components)

        
    async def wait_bet(self):
        while True:
            await self.update_bet_menu()
            interaction:Interaction = await self.bot.wait_for('select_option', check=lambda i: i.user.id in self.players)
            user_id = interaction.user.id
            bet = interaction.component[0].value
            bet = int(bet)

            user_chips = self.server[str(self.guild_id)]['users'][str(user_id)]['casino']['chips']
            if user_chips < bet:
                await interaction.respond(content='Недостаточно фишек!')
                continue
            if not interaction.responded:
                await interaction.respond(type=6)
             
            self.current_players[str(user_id)]['bet'] = bet

            for player in self.current_players:
                player_bet = self.current_players[player]['bet']
                if player_bet == 'Нет ставки':
                    break
            else:
                await self.update_bet_menu()
                return


    def player_take_card(self, member_id):
        card = choice(self.available_cards)
        self.available_cards.remove(card)
        self.current_players[str(member_id)]['cards'].append(card)
        self.current_players[str(member_id)]['sum_cards'] += self.all_nums[card[1:]]
        return card


    def diler_take_card(self):
        card = choice(self.available_cards)
        self.available_cards.remove(card)
        self.diler_cards_list.append(card)
        self.sum_diler_cards += self.all_nums[card[1:]]
        return card


    async def out_score(self, ctx:commands.Context):
        embed = discord.Embed(title='Блэкджек. Итоги игры', color=get_embed_color(self.guild_id))
        embed.description = f'**Игрок** | **Статус** | **Причина** | **Выигрыш**'
        diler_sum = self.sum_diler_cards
        for _player in self.current_players:
            player = self.current_players[_player]
            user_casino = self.server[str(self.guild_id)]['users'][str(_player)]['casino']
            sum_cards = player['sum_cards']

            if sum_cards > 21:
                player_score = f'\n{player["nickname"]} | Проиграл | Перебор карт | {player["bet"] * (-1)} `фишек`'
                user_casino['chips'] += player["bet"] * (+1)
                
            elif sum_cards < diler_sum and diler_sum <= 21:
                player_score = f'\n{player["nickname"]} | Проиграл | Сумма карт меньше, чем у Дилера | {player["bet"] * (-1)} `фишек`'
                user_casino['chips'] += player["bet"] * (-1)
                
            elif sum_cards > diler_sum and sum_cards < 21:
                player_score = f'\n{player["nickname"]} | Выиграл | Сумма карт больше, чем у Дилера | {player["bet"] * 2} `фишек`'
                user_casino['chips'] += player["bet"] * 2
                
            elif sum_cards < diler_sum:
                player_score = f'\n{player["nickname"]} | Выиграл | У Дилера перебор | {player["bet"] * 2} `фишек`'
                user_casino['chips'] += player["bet"] * 2
                
            elif sum_cards == diler_sum:
                player_score = f'\n{player["nickname"]} | Ничья | Сумма карт равны | {0} `фишек`'
                
            elif sum_cards == 21 or (sum_cards == 22 and len(player['cards']) == 2):
                player_score = f'\n{player["nickname"]} | Выиграл | Блэкджек | {player["bet"] * 3} `фишек`'
                user_casino['chips'] += player["bet"] * 3
            else:
                player_score = f'Неизвестное условие!'
            embed.description += player_score

        await self.message.edit(components=[])
        await ctx.send(embed=embed)
