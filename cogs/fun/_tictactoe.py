from discord import Embed, Member
from discord_components import Button, ButtonStyle
from discord_slash.context import SlashContext
from discord_slash_components_bridge import (
    ComponentMessage,
    ComponentContext
)

from my_utils import AsteroidBot


class TicTacToe:
    def __init__(
        self,
        bot: AsteroidBot,
        message: ComponentMessage,
        ctx: SlashContext,
        member: Member,
        content: dict
        ) -> None:
        self.bot = bot
        self.message = message
        self.ctx = ctx
        self.member = member
        self.content = content

    async def start_game(self):
        self.create_boards()

        await self.message.edit(content=self.content['GAME_NAME'], components=self.game_board)

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
        self.game_board = []
        self.move_board = []
        for i in range(3):
            self.game_board.insert(i, [])
            self.move_board.insert(i, [])
            for j in range(3):
                self.game_board[i].insert(j, Button(style=ButtonStyle.gray, label=' ', id=f'{i} {j}'))
                self.move_board[i].insert(j, 'UNCHOSEN')


    def _check(self, player_id, interaction):
        return interaction.author_id == player_id and interaction.message.id == self.message.id


    async def move(self, player_game_name, emoji_id, player):
        style = ButtonStyle.green if player_game_name == 'player_1' else ButtonStyle.red
        check = lambda interaction: self._check(player.id, interaction)

        interaction: ComponentContext = await self.bot.wait_for('button_click', check=check)
        await interaction.defer(edit_origin=True)

        move_id = interaction.component.id
        pos1, pos2 = move_id.split(' ')
        self.game_board[int(pos1)][int(pos2)] = Button(
            style=style, emoji=self.bot.get_emoji(emoji_id), disabled=True)

        await interaction.edit_origin(components=self.game_board)
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


    async def pick_a_winner(self, winner='_draw'):
        if winner == '_draw':
            winner = self.content['RESULTS_TIE']

        embed = Embed(
            title=self.content['RESULTS_TITLE'],
            color=self.bot.get_embed_color(self.ctx.guild_id))
        embed.add_field(
            name=self.content['RESULTS_GAME_NAME'],
            value=self.content['RESULTS_TEXT'].format(
                player1=self.member.display_name,
                player2=self.ctx.author.display_name,
                winner=winner
            )
        )

        for row in self.game_board:
            for button in row:
                button.disabled = True

        await self.message.edit(content=' ', embed=embed, components=self.game_board)