from discord import Embed
from discord_components import Button, ButtonStyle, Interaction
from .bot_settings import get_embed_color



class TicTacToe:
    def __init__(self, bot, message, ctx, member) -> None:
        self.bot = bot
        self.message = message
        self.ctx = ctx
        self.member = member

    async def start_game(self):
        self.board, self.move_board = self.create_boards()

        await self.message.edit(content='Крестики-Нолики', components=self.board)

        player_1_move = True
        while True:
            if player_1_move:
                result = await self.move('player_1', 850792048080060456, self.member)
                player_1_move = False
                if result:
                    return
            if not player_1_move:
                result = await self.move('player_2', 850792047698509826, self.ctx.author)
                player_1_move = True
                if result:
                    return


    def create_boards(self):
        game_board = []
        move_board = []
        for i in range(3):
            game_board.insert(i, [])
            move_board.insert(i, [])
            for j in range(3):
                game_board[i].insert(j, Button(style=ButtonStyle.gray, label=' ', id=f'{i} {j}'))
                move_board[i].insert(j, 'UNCHOSEN')
        return game_board, move_board


    def player_1(self, interaction):
            return interaction.user.id == self.member.id

    def player_2(self, interaction):
        return interaction.user.id == self.ctx.author.id

    async def move(self, player_id, emoji_id, player):
        if player_id == 'player_1':
            check = self.player_1
            style = ButtonStyle.green
        else:
            check = self.player_2
            style = ButtonStyle.red

        interaction:Interaction = await self.bot.wait_for('button_click', check=check)
        await interaction.respond(type=6)

        move_id = interaction.component.id
        pos1, pos2 = move_id.split(' ')
        self.board[int(pos1)][int(pos2)] = Button(
            style=style, emoji=self.bot.get_emoji(emoji_id), id='0', disabled=True)

        await self.message.edit(components=self.board)
        self.move_board[int(pos1)][int(pos2)] = player

        if self.is_won(player):
            await self.pick_a_winner(player.display_name)
            return True
        elif self.is_tie(player):
            await self.pick_a_winner()
            return True
        return False


    def is_won(self, player):
        if self.move_board[0][0] == player and self.move_board[0][1] == player and self.move_board[0][2] == player:
            return True
        if self.move_board[1][0] == player and self.move_board[1][1] == player and self.move_board[1][2] == player:
            return True
        if self.move_board[2][0] == player and self.move_board[2][1] == player and self.move_board[2][2] == player:
            return True
        if self.move_board[0][0] == player and self.move_board[1][0] == player and self.move_board[2][0] == player:
            return True
        if self.move_board[0][1] == player and self.move_board[1][1] == player and self.move_board[2][1] == player:
            return True
        if self.move_board[0][2] == player and self.move_board[1][2] == player and self.move_board[2][2] == player:
            return True
        if self.move_board[0][0] == player and self.move_board[1][1] == player and self.move_board[2][2] == player:
            return True
        if self.move_board[0][2] == player and self.move_board[1][1] == player and self.move_board[2][0] == player:
            return True
        return False

    def is_tie(self, player):
        return "UNCHOSEN" not in str(self.move_board) and not self.is_won(player)


    async def pick_a_winner(self, winner='Ничья'):
        embed = Embed(
            title='`          ИТОГИ ИГРЫ            `', color=get_embed_color(self.ctx.guild.id))
        embed.add_field(name=f'**Название: Крестики-Нолики**',
                        value=f"""
                        **Игроки: {self.member.display_name} и {self.ctx.author.display_name}**
                        **Победитель:** {winner}
                        """)
        for row in self.board:
            for button in row:
                button.disabled = True
        await self.message.edit(content=' ', embed=embed, components=self.board)