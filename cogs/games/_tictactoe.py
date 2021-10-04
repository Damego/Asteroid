from discord import Embed
from discord_slash import ButtonStyle
from discord_components import Button

from discord_slash.utils.manage_components import (
    create_button as Button1,
    create_actionrow as ActionRow,
    wait_for_component,
    spread_to_rows
)




class TicTacToe:
    def __init__(self, bot, message, ctx, member) -> None:
        self.bot = bot
        self.message = message
        self.ctx = ctx
        self.member = member

    async def start_game(self):
        self.create_boards()
        action_rows = spread_to_rows(*self.game_board, max_in_row=3)

        await self.message.edit(content='Крестики-Нолики', components=action_rows)

        player_1_move = True
        while True:
            if player_1_move:
                result = await self.move('player_1', self.member)
                player_1_move = False
            if not player_1_move:
                result = await self.move('player_2', self.ctx.author)
                player_1_move = True
            if result:
                return


    def create_boards(self):
        game_board = []
        move_board = []
        for i in range(3):
            move_board.insert(i, [])
            for j in range(3):
                game_board.append(Button(style=ButtonStyle.gray, label=' ', custom_id=f'{i} {j}'))
                move_board[i].insert(j, 'UNCHOSEN')
            
        self.game_board = game_board
        self.move_board = move_board


    def player_1(self, interaction):
        return interaction.author.id == self.member.id

    def player_2(self, interaction):
        return interaction.author.id == self.ctx.author.id

    async def move(self, player_id, player):
        if player_id == 'player_1':
            check = self.player_1
            style = ButtonStyle.blue
        else:
            check = self.player_2
            style = ButtonStyle.red

        interaction = await wait_for_component(self.bot, self.message, spread_to_rows(*self.game_board, max_in_row=3), check=check)
        await interaction.defer(ignore=True)

        move_id = interaction.custom_id
        pos1, pos2 = move_id.split(' ')
        for component in self.game_board:
            if component['custom_id'] == move_id:
                self.game_board[self.game_board.index(component)] = Button(
                    label=' ', style=style, disabled=True
                )   
                break
        action_rows = spread_to_rows(*self.game_board, max_in_row=3)

        await self.message.edit(components=action_rows)

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
            title='`          ИТОГИ ИГРЫ            `',
            color=self.bot.get_embed_color(self.ctx.guild.id))
        embed.add_field(name=f'**Название: Крестики-Нолики**',
            value=f"""
            **Игроки: {self.member.display_name} и {self.ctx.author.display_name}**
            **Победитель:** {winner}
            """)
        for component in self.game_board:
            component['disabled'] = True
        action_rows = spread_to_rows(*self.game_board, max_in_row=3)
        await self.message.edit(content=' ', embed=embed, components=action_rows)