import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle

from extensions.bot_settings import get_embed_color, get_db

server = get_db

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

    def rps_who_won(self, ctx, member):
        """Определяет по очкам, кто в итоге победил, и возвращает ник"""
        if self.count1 > self.count2:
            return ctx.author.display_name
        elif self.count1 < self.count2:
            return member
        return 'Ничья'

    
    async def rps_game_logic(self, ctx, msg, member, round, total_rounds):
        def player_1(res):
            return res.user == member
        def player_2(res):
            return res.user == ctx.author
        
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
        res1 = await self.bot.wait_for("button_click", check=player_1)
        await res1.respond(type=6)
        res2 = await self.bot.wait_for("button_click", check=player_2)
        await res2.respond(type=6)

        await self.rps_check_results(res1, res2)

    @commands.command(description='Запускает игру Камень-ножницы-бумага\nПервый ход получает тот, кого пригласили в игру', help='[ник] [кол-во игр]')
    async def rps(self, ctx, member:discord.Member, total_rounds:int=1):
        if member == ctx.author:
            await ctx.send('Вы не можете пригласить себя!')
            return
        self.count1 = 0
        self.count2 = 0

        msg, accept = await self.invite_to_game(ctx, member, 'Камень-Ножницы-Бумага')

        if not accept:
            await msg.delete()
            await ctx.send(f'{member} отказался от игры')
            return

        for round in range(total_rounds):
            await self.rps_game_logic(ctx, msg, member, round, total_rounds)

        winner = self.rps_who_won(ctx, member)

        embed = discord.Embed(title='`          ИТОГИ ИГРЫ            `')
        embed.add_field(name=f'**Название игры: Камень-ножницы-бумага**',
                        value=f"""
                        **Игроки: {ctx.author.display_name} и {member.display_name}**
                        **Количество сыгранных игр:** {total_rounds}
                        **Счёт:** {self.count1}:{self.count2}
                        **Победитель:** {winner}
                        """
        )
        await msg.edit(content='Игра закончилась!',embed=embed, components=[])


    @commands.command(description='Запускает игру Крестики-Нолики \nПервый ход получает тот, кого пригласили в игру', help='[ник]')
    async def ttt(self, ctx, member:discord.Member):
        if member == ctx.author:
            await ctx.send('Вы не можете пригласить себя!')
            return
        msg, accept = await self.invite_to_game(ctx, member, 'Крестики-Нолики')
        if not accept:
            return

        def player_1(res):
            return res.user.id == member.id
        def player_2(res):
            return res.user.id == ctx.author.id
    
        async def move(player_id, emoji_id, player):
            if player_id == 'player_1':
                check = player_1
                style = ButtonStyle.green
            elif player_id == 'player_2':
                check = player_2
                style = ButtonStyle.red
            
            res = await self.bot.wait_for('button_click', check=check)
            await res.respond(type=6)

            move_id = res.component.id
            pos1, pos2 = move_id.split(' ')
            board[int(pos1)][int(pos2)] = Button(style=style, emoji=self.bot.get_emoji(emoji_id), id='0', disabled=True)

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
            move_board.insert(i,[])
            for j in range(3):
                move_board[i].insert(j,'UNCHOSEN')

        def is_won(player):
            for i in range(3):
                for j in range(3):
                    if move_board[i][j] == player:
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
            board.insert(i,[])
            for j in range(3):
                board[i].insert(j, Button(style=ButtonStyle.gray, label=' ', id=f'{i} {j}'))


        await msg.edit(content='Крестики-Нолики',components=board)

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
        embed = discord.Embed(title='`          ИТОГИ ИГРЫ            `', color=get_embed_color(ctx.message))
        embed.add_field(name=f'**Название: Крестики-Нолики**',
                        value=f"""
                        **Игроки: {player1.display_name} и {player2.display_name}**
                        **Победитель:** {winner}
                        """)
        await msg.edit(content=' ', embed=embed)


    async def invite_to_game(self, ctx, member, game_name):
        def member_agree(res):
            return res.user.id == member.id and res.channel.id == ctx.channel.id and res.message.id == msg.id

        msg = await ctx.send(
            content=f"{member.mention}! {ctx.author.name} приглашает тебя в игру {game_name}",
            components=[
                [
                    Button(style=ButtonStyle.green, label='Согласиться', id=1),
                    Button(style=ButtonStyle.red, label='Отказаться', id=2)
                ]])

        try:
            res = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
        except TimeoutError:
            await msg.edit(content=f'От {member.display_name} нет ответа!')
            return msg, False
        await res.respond(type=6)
        if res.component.id == '1':
            embed = discord.Embed(title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}',color=get_embed_color(ctx.message))
            await msg.edit(context=' ', embed=embed)
            return msg, True
        await msg.edit(content=f'{member.display_name} отказался от игры!', components=[])
        return msg, False

def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Games(bot))