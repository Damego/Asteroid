from random import choice

import discord
from discord_components import DiscordComponents, Button, ButtonStyle
from discord.ext import commands

from extensions.bot_settings import get_embed_color, get_db

server = get_db


class Games(commands.Cog, description='Игры'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['games']

    async def rps_logic(self, player_1_interact, player_2_interact):
        """Проверяет ходы участников и даёт очко тому, кто выиграл"""
        if player_1_interact.component.id == player_2_interact.component.id:
            return
        elif player_1_interact.component.id == '1':
            if player_2_interact.component.id == '3':
                self.count1 += 1
                return
            self.count2 += 1
            return
        elif player_1_interact.component.id == '2':
            if player_2_interact.component.id == '1':
                self.count1 += 1
                return
            self.count2 += 1
            return
        elif player_1_interact.component.id == '3':
            if player_2_interact.component.id == '2':
                self.count1 += 1
                return
            self.count2 += 1
            return

    def rps_winner(self, ctx, member):
        """Определяет по очкам, кто в итоге победил, и возвращает победителя"""
        if self.count1 > self.count2:
            return ctx.author.display_name
        elif self.count1 < self.count2:
            return member
        return 'Ничья'

    async def rps_run_game(self, ctx, msg, member, round, total_rounds):
        def player_1(interaction):
            return interaction.user == member

        def player_2(interaction):
            return interaction.user == ctx.author

        embed = discord.Embed(title='🪨-✂️-🧾')
        embed.add_field(name=f'**{ctx.author.display_name}** VS **{member.display_name}**',
                        value=f'**Счёт:** {self.count1}:{self.count2} \n**Игра:** {round+1}/{total_rounds}'
                        )
        await msg.edit(
            content='Идёт игра...',
            embed=embed,
            components=[
                [
                    Button(style=ButtonStyle.gray, id=1, emoji='🪨'),
                    Button(style=ButtonStyle.gray, id=2, emoji='🧾'),
                    Button(style=ButtonStyle.gray, id=3, emoji='✂️')
                ]])
        player_1_interact = await self.bot.wait_for("button_click", check=player_1)
        await player_1_interact.respond(type=6)
        player_2_interact = await self.bot.wait_for("button_click", check=player_2)
        await player_2_interact.respond(type=6)

        await self.rps_logic(player_1_interact, player_2_interact)

    @commands.command(aliases=['rps'], description='Запускает игру Камень-ножницы-бумага\nПервый ход получает тот, кого пригласили в игру', help='[ник] [кол-во игр]')
    async def rockpaperscissors(self, ctx, member: discord.Member, total_rounds: int = 1):
        if member == ctx.author:
            await ctx.send('Вы не можете пригласить себя!')
            return
        self.count1 = 0
        self.count2 = 0

        msg, accept = await self.invite_to_game(ctx, member, 'Камень-Ножницы-Бумага')

        if not accept:
            await msg.delete()
            await msg.edit(content=f'{member} отказался от игры', components=[])
            return

        for round in range(total_rounds):
            await self.rps_run_game(ctx, msg, member, round, total_rounds)

        winner = self.rps_winner(ctx, member)

        embed = discord.Embed(title='`          ИТОГИ ИГРЫ            `')
        embed.add_field(name=f'**Название игры: Камень-ножницы-бумага**',
                        value=f"""
                        **Игроки: {ctx.author.display_name} и {member.display_name}**
                        **Количество сыгранных игр:** {total_rounds}
                        **Счёт:** {self.count1}:{self.count2}
                        **Победитель:** {winner}
                        """
                        )
        await msg.edit(content='Игра закончилась!', embed=embed, components=[])

    @commands.command(aliases=['ttt'], description='Запускает игру Крестики-Нолики \nПервый ход получает тот, кого пригласили в игру', help='[ник]')
    async def tictactoe(self, ctx, member: discord.Member):
        if member == ctx.author:
            await ctx.send('Вы не можете пригласить себя!')
            return
        msg, accept = await self.invite_to_game(ctx, member, 'Крестики-Нолики')
        if not accept:
            return

        def player_1(interaction):
            return interaction.user.id == member.id

        def player_2(interaction):
            return interaction.user.id == ctx.author.id

        async def move(player_id, emoji_id, player):
            if player_id == 'player_1':
                check = player_1
                style = ButtonStyle.green
            elif player_id == 'player_2':
                check = player_2
                style = ButtonStyle.red

            interaction = await self.bot.wait_for('button_click', check=check)
            await interaction.respond(type=6)

            move_id = interaction.component.id
            pos1, pos2 = move_id.split(' ')
            board[int(pos1)][int(pos2)] = Button(
                style=style, emoji=self.bot.get_emoji(emoji_id), id='0', disabled=True)

            await msg.edit(components=board)
            move_board[int(pos1)][int(pos2)] = player

            if is_won(player):
                await self.pick_a_winner(msg, ctx, member, ctx.author, player.display_name)
                return
            if is_tie(player):
                await self.pick_a_winner(msg, ctx, member, ctx.author)
                return

        move_board = []
        for i in range(3):
            move_board.insert(i, [])
            for j in range(3):
                move_board[i].insert(j, 'UNCHOSEN')

        def is_won(player):
            if move_board[0][0] == player and move_board[0][1] == player and move_board[0][2] == player:
                return True
            if move_board[1][0] == player and move_board[1][1] == player and move_board[1][2] == player:
                return True
            if move_board[2][0] == player and move_board[2][1] == player and move_board[2][2] == player:
                return True
            if move_board[0][0] == player and move_board[1][0] == player and move_board[2][0] == player:
                return True
            if move_board[0][1] == player and move_board[1][1] == player and move_board[2][1] == player:
                return True
            if move_board[0][2] == player and move_board[1][2] == player and move_board[2][2] == player:
                return True
            if move_board[0][0] == player and move_board[1][1] == player and move_board[2][2] == player:
                return True
            if move_board[0][2] == player and move_board[1][1] == player and move_board[2][0] == player:
                return True
            return False

        def is_tie(player):
            if not "UNCHOSEN" in str(move_board):
                if not is_won(player):
                    return True
                return False
            return False

        board = []

        for i in range(3):
            board.insert(i, [])
            for j in range(3):
                board[i].insert(
                    j, Button(style=ButtonStyle.gray, label=' ', id=f'{i} {j}'))

        await msg.edit(content='Крестики-Нолики', components=board)

        player_1_move = True
        while accept:
            if player_1_move:
                result = await move('player_1', 850792048080060456, member)
                player_1_move = False
                if result == 'Game_end':
                    return
            if not player_1_move:
                result = await move('player_2', 850792047698509826, ctx.author)
                player_1_move = True
                if result == 'Game_end':
                    return

    async def pick_a_winner(self, msg, ctx, player1, player2, winner='Ничья'):
        embed = discord.Embed(
            title='`          ИТОГИ ИГРЫ            `', color=get_embed_color(ctx.guild.id))
        embed.add_field(name=f'**Название: Крестики-Нолики**',
                        value=f"""
                        **Игроки: {player1.display_name} и {player2.display_name}**
                        **Победитель:** {winner}
                        """)
        await msg.edit(content=' ', embed=embed)

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

        try:
            interaction = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
            await interaction.respond(type=6)
        except TimeoutError:
            await msg.edit(content=f'От {member.display_name} нет ответа!')
            return msg, False

        if interaction.component.id == '1':
            embed = discord.Embed(
                title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}', color=get_embed_color(ctx.guild.id))
            await msg.edit(context=' ', embed=embed)
            return msg, True

        await msg.edit(content=f'{member.display_name} отказался от игры!', components=[])
        return msg, False

    @commands.command(name='game_21', description='', help='', hidden=True)
    async def game_21(self, ctx):
        async def is_end(diler_move=False):
            # ? maybe remove `ctx.send` and take out in separate function?
            if not diler_move:
                if sum_user_cards == 21:
                    await ctx.send('У вас 21! Вы выиграли!')
                    return True
                elif sum_user_cards > 21:
                    await ctx.send('У вас перебор! Вы проиграли')
                    return True

            if diler_move:
                if sum_diler_cards == 21:
                    await ctx.send('у Дилера 21 очко! Вы проиграли!')
                    return True
                elif sum_diler_cards > 21:
                    await ctx.send('У Дилера перебор! Вы выиграли!')
                    return True
                elif sum_user_cards == sum_diler_cards:
                    await ctx.send('Ничья!')
                    return True
                elif sum_diler_cards > sum_user_cards:
                    await ctx.send('Вы проиграли! Сумма ваших карт меньше, чем у Дилера!')
                    return True
                elif sum_diler_cards < sum_user_cards:
                    await ctx.send('Вы выиграли! Сумма ваших карт больше, чем у Дилера!')
                    return True
            return False

        async def update_message(diler_move=False, remove_buttons=False):
            if not diler_move:
                diler_cards_str = ', '.join(hidden_card_list)
                sum_diler_cards = hidden_sum_diler_cards
            if diler_move:
                diler_cards_str = ', '.join(diler_cards_list)
                sum_diler_cards = diler_sum

            embed = discord.Embed(title='21 Очко')
            embed.add_field(
                name='Карты дилера:', value=f'{diler_cards_str}\nСумма карт: {sum_diler_cards}', inline=False)
            embed.add_field(
                name='Ваши карты:', value=f'{user_cards_str}\nСумма карт: {sum_user_cards}', inline=False)
            if remove_buttons:
                components = []
            else: # ? Wat?
                components = bcomponents

            await msg.edit(content=' ', embed=embed, components=components)

        spades = {'♠6', '♠7', '♠8', '♠9', '♠10', '♠В', '♠Д', '♠К', '♠Т'}
        clubs = {'♣6', '♣7', '♣8', '♣9', '♣10', '♣В', '♣Д', '♣К', '♣Т'}
        hearts = {'♥6', '♥7', '♥8', '♥9', '♥10', '♥В', '♥Д', '♥К', '♥Т'}
        diamonds = {'♦6', '♦7', '♦8', '♦9', '♦10', '♦В', '♦Д', '♦К', '♦Т'}
        all_cards = list(spades) + list(clubs) + list(hearts) + list(diamonds)

        all_nums = {
            '6': 6,
            '7': 7,
            '8': 8,
            '9': 9,
            '10': 10,
            'В': 2,
            'Д': 3,
            'К': 4,
            'Т': 11,
        }

        buttons = [[
            Button(style=ButtonStyle.green, label='Начать игру', id='1'),
            Button(style=ButtonStyle.red, label='Выйти из игры', id='2'),
        ]]

        msg = await ctx.send(content='21 Очко (Блэкджек)', components=buttons)

        interaction = await self.bot.wait_for('button_click', check=lambda i: i.user.id == ctx.author.id)
        await interaction.respond(type=6)

        if interaction.component.id == '2':
            await msg.delete()
            return

        bcomponents = [[ # ? bcomponents? What?
            Button(style=ButtonStyle.blue,
                    label='Взять карту', id='1'),
            Button(style=ButtonStyle.blue,
                    label='Передать ход', id='2'),
            Button(style=ButtonStyle.red,
                    label='Выйти из игры', id='3'),
                ]]

        user_cards_list = []
        sum_user_cards = 0
        diler_cards_list = []
        hidden_card_list = []
        sum_diler_cards = 0
        hidden_sum_diler_cards = 0
        taking_card_loop = 0

        while True:
            while taking_card_loop != 2: # * Maybe better is `< 2` ?
                # ! Need refactor code and optimizing!
                card = choice(all_cards)
                all_cards.remove(card) 
                user_cards_list.append(card)
                sum_user_cards += all_nums[card[1:]]

                card = choice(all_cards)
                all_cards.remove(card)
                diler_cards_list.append(card)
                sum_diler_cards += all_nums[card[1:]]
                if taking_card_loop < 1:
                    hidden_sum_diler_cards += all_nums[card[1:]]
                    hidden_card_list.append(card)
                    hidden_card_list.append('?')

                taking_card_loop += 1

            user_cards_str = ', '.join(user_cards_list)

            await update_message()

            if all_nums[user_cards_list[0][1:]] == 11 and all_nums[user_cards_list[1][1:]] == 11:
                # TODO : Why It's now working? Check and fix it!
                if all_nums[card[1:]] == 11:
                    bcomponents.append(
                        Button(style=ButtonStyle.green, label='Мягкий туз', id='4')
                    )
                    await msg.edit(components=bcomponents)
            else:
                isend = await is_end()
                if isend:
                    hidden_card_list = diler_cards_list.copy()
                    diler_sum = sum_diler_cards
                    await update_message(remove_buttons=True)
                    return

            interaction = await self.bot.wait_for('button_click', check=lambda i: i.user.id == ctx.author.id)
            await interaction.respond(type=6)

            if interaction.component.id == '1':
                card = choice(all_cards)
                user_cards_list.append(card)
                sum_user_cards += all_nums[card[1:]]

                user_cards_str = ', '.join(user_cards_list)

                await update_message()


                # ? Maybe add this in separate function?
                if all_nums[card[1:]] == 11:
                    bcomponents.append(
                        Button(style=ButtonStyle.green, label='Мягкий туз', id='4')
                    )
                    await msg.edit(components=bcomponents)
                    
                else:
                    isend = await is_end()
                    if isend:
                        hidden_card_list = diler_cards_list.copy()
                        diler_sum = sum_diler_cards
                        await update_message(remove_buttons=True)
                        return

            elif interaction.component.id == '2':
                while True:
                    if sum_diler_cards < 17:
                        # ! Separate Func!
                        card = choice(all_cards)
                        all_cards.remove(card)
                        diler_cards_list.append(card)
                        sum_diler_cards += all_nums[card[1:]]
                        diler_sum = sum_diler_cards
                        await update_message(True)

                    elif sum_diler_cards > 16:
                        isend = await is_end(True)
                        if isend:
                            diler_sum = sum_diler_cards
                            await update_message(True, True) # ? : Maybe take out this method out of the loop?
                            return
            elif interaction.component.id == '3':
                await msg.delete()
                return
                
            elif interaction.component.id == '4':
                sum_diler_cards -= 10
                await update_message()
                bcomponents.pop(3)



def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Games(bot))
