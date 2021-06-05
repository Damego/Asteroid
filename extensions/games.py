from discord_slash import context
from extensions.music import get_embed_color
import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle

class Games(commands.Cog, description='Игры'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False


    async def rps_check_results(self, res1, res2):
        """Проверяет ходы участников и даёт очко тому, кто выиграл"""
        if res1.component.id == res2.component.id:
            return
        elif res1.component.id == '1':
            if res2.component.id == '3':
                self.count1 +=1
                return 
            self.count2 +=1
            return 
        elif res1.component.id == '2':
            if res2.component.id == '1':
                self.count1 +=1
                return 
            self.count2 +=1
            return 
        elif res1.component.id == '3':
            if res2.component.id == '2':
                self.count1 +=1
                return 
            self.count2 +=1
            return 

    async def rps_who_won(self, ctx, res):
        """Определяет по очкам, кто в итоге победил, и возвращает ник"""
        if self.count1 > self.count2:
            return ctx.author.display_name
        elif self.count1 < self.count2:
            return res.user
        return 'Ничья'

        

    async def rps_game_logic(self, ctx, msg, member, game_number, quantity):
        def player_1(res):
            if res.user == ctx.author:
                return res.component.id
        def player_2(res):
            if res.user == member:
                return res.component.id

        embed = discord.Embed(title='🪨-✂️-🧾')
        embed.add_field(name=f'**{ctx.author.display_name}** VS **{member.display_name}**',
                        value=f'**Счёт:** {self.count1}:{self.count2} \n**Игра:** {game_number+1}/{quantity}'
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
        res1 = await self.bot.wait_for("button_click", check=player_1)
        res2 = await self.bot.wait_for("button_click", check=player_2)

        await self.rps_check_results(res1, res2)

    @commands.command(description='Запускает игру Камень-ножницы-бумага\nПервый ход получает тот, кого пригласили в игру', help='[ник] [кол-во игр]')
    async def rps(self, ctx, member:discord.Member, quantity:int=1):
        self.count1 = 0
        self.count2 = 0

        def member_agree(res):
            return member == res.user

        msg = await ctx.send(
            f"{member.mention}! {ctx.author.name} приглашает тебя в игру Камень-ножницы-бумага",
            components=[
                [
                    Button(style=ButtonStyle.green, label='Согласиться', id=1),
                    Button(style=ButtonStyle.red, label='Отказаться', id=2)
                ]])

        try:
            res = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
        except Exception:
            res = None
        if res.component.id == '1':
            for game_number in range(quantity):
                await self.rps_game_logic(ctx, msg, member, game_number, quantity)

            winner = await self.rps_who_won(ctx, res)

            embed = discord.Embed(title='`          ИТОГИ ИГРЫ            `')
            embed.add_field(name=f'**Название игры: Камень-ножницы-бумага**',
                            value=f"""
                            **Игроки: {ctx.author.display_name} и {member.display_name}**
                            **Количество сыгранных игр:** {quantity}
                            **Счёт:** {self.count1}:{self.count2}
                            **Победитель:** {winner}
                            """
            )
            await msg.edit(content='Игра закончилась!',embed=embed, components=[])
        else:
            await msg.delete()
            await ctx.send(f'{res.user} отказался от игры')

    @commands.command(description='Запускает игру Крестики-Нолики \nПервый ход получает тот, кого пригласили в игру', help='[ник]')
    async def ttt(self, ctx, member:discord.Member):
        def member_agree(res):
            return member == res.user

        msg = await ctx.send(
            f"{member.mention}! {ctx.author.name} приглашает тебя в игру Крестики-Нолики",
            components=[
                [
                    Button(style=ButtonStyle.green, label='Согласиться', id=1),
                    Button(style=ButtonStyle.red, label='Отказаться', id=2)
                ]])

        try:
            res = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
            await res.respond(type=6)
            if res.component.id == '1':
                accept = True
                embed = discord.Embed(title='Крестики-Нолики', description=f'{ctx.author.display_name} VS {member.display_name}',color=get_embed_color(ctx.message))
                await msg.edit(context=' ', embed=embed)
            else:
                await msg.edit(content=f'{member.display_name} отказался от игры!')
                return
        except:
            await msg.edit(content=f'От {member.display_name} нет ответа!')
            return


        def player_1(res):
            if res.user == member:
                return res.component.id
        def player_2(res):
            if res.user == ctx.author:
                return res.component.id

        move_board = [
            [
                'UNCHOSEN',
                'UNCHOSEN',
                'UNCHOSEN',
            ],
            [
                'UNCHOSEN',
                'UNCHOSEN',
                'UNCHOSEN',
            ],
            [
                'UNCHOSEN',
                'UNCHOSEN',
                'UNCHOSEN',
            ]
        ]


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
            else:
                return False

        def is_tie(player):
            if not "UNCHOSEN" in str(move_board):
                if not is_won(player):
                    return True
                return False
            return False

        board = [
            [
                Button(style=ButtonStyle.gray, label='\u200b', id='0 0'),
                Button(style=ButtonStyle.gray, label='\u200b', id='0 1'),
                Button(style=ButtonStyle.gray, label='\u200b', id='0 2'),
            ],
            [
                Button(style=ButtonStyle.gray, label='\u200b', id='1 0'),
                Button(style=ButtonStyle.gray, label='\u200b', id='1 1'),
                Button(style=ButtonStyle.gray, label='\u200b', id='1 2'),
            ],
            [
                Button(style=ButtonStyle.gray, label='\u200b', id='2 0'),
                Button(style=ButtonStyle.gray, label='\u200b', id='2 1'),
                Button(style=ButtonStyle.gray, label='\u200b', id='2 2'),
            ],
        ]

        await msg.edit(content='Крестики-Нолики',components=board)

        player_1_move = True
        while accept:
            if player_1_move:
                res = await self.bot.wait_for('button_click', check=player_1)
                await res.respond(type=6)
                move_id = res.component.id
                pos1, pos2 = move_id.split(' ')
                board[int(pos1)][int(pos2)] = Button(style=ButtonStyle.green, emoji=self.bot.get_emoji(850792048080060456), id='0', disabled=True)
                await msg.edit(components=board)
                move_board[int(pos1)][int(pos2)] = 'Player_1'
                if is_won('Player_1'):
                    await self.pick_a_winner(msg, ctx, member, ctx.author, member.display_name)
                    return
                if is_tie('Player_1'):
                    await self.pick_a_winner(msg, ctx, member, ctx.author)
                    return
                player_1_move = False
            if not player_1_move:
                res = await self.bot.wait_for('button_click', check=player_2)
                await res.respond(type=6)
                move_id = res.component.id
                pos1, pos2 = move_id.split(' ')
                board[int(pos1)][int(pos2)] = Button(style=ButtonStyle.red, emoji=self.bot.get_emoji(850792047698509826), id='0', disabled=True)
                await msg.edit(components=board)
                move_board[int(pos1)][int(pos2)] = 'Player_2'
                if is_won('Player_2'):
                    await self.pick_a_winner(msg, ctx, member, ctx.author, ctx.author.display_name)
                    return
                if is_tie('Player_2'):
                    await self.pick_a_winner(msg, ctx, member, ctx.author)
                    return
                player_1_move = True


    async def pick_a_winner(self, msg, ctx, player1, player2, winner='Ничья'):
        embed = discord.Embed(title='`          ИТОГИ ИГРЫ            `', color=get_embed_color(ctx.message))
        embed.add_field(name=f'**Название: Крестики-Нолики**',
                        value=f"""
                        **Игроки: {player1.display_name} и {player2.display_name}**
                        **Победитель:** {winner}
                        """)
        await msg.edit(content=' ', embed=embed)




def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Games(bot))