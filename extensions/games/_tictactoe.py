from discord import Embed
from discord_components import Button, ButtonStyle, Interaction




class TicTacToe:
    def __init__(self, bot, message, ctx, member) -> None:
        self.bot = bot
        self.message = message
        self.ctx = ctx
        self.member = member

    async def start_game(self):
        self.board, self.move_board = self.create_boards()

        await self.message.edit(content='Tic Tac Toe', components=self.board)

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


    def _check(self, player_id, interaction):
        return interaction.user.id == player_id and interaction.message.id == self.message.id


    async def move(self, player_game_name, emoji_id, player):
        style = ButtonStyle.green if player_game_name == 'player_1' else ButtonStyle.red
        check = lambda interaction: self._check(player.id, interaction)

        interaction:Interaction = await self.bot.wait_for('button_click', check=check)
        await interaction.respond(type=6)

        move_id = interaction.component.id
        pos1, pos2 = move_id.split(' ')
        self.board[int(pos1)][int(pos2)] = Button(
            style=style, emoji=self.bot.get_emoji(emoji_id), disabled=True)

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


    async def pick_a_winner(self, winner='Draw'):
        embed = Embed(
            title='`          Results            `', color=self.bot.get_embed_color(self.ctx.guild.id))
        embed.add_field(name=f'**Name: Tic Tac Toe**',
                        value=f"""
                        **Players: {self.member.display_name} and {self.ctx.author.display_name}**
                        **Winner:** {winner}
                        """)
        for row in self.board:
            for button in row:
                button.disabled = True
        await self.message.edit(content=' ', embed=embed, components=self.board)