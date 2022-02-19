from copy import deepcopy
from enum import IntEnum
from typing import List

from discord import Embed, Member
from discord_slash import (
    SlashContext,
    ComponentMessage,
    ComponentContext,
    Button,
    ButtonStyle,
)

from my_utils import AsteroidBot


board_template = {
    3: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
    4: [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    5: [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
}


class GameState(IntEnum):
    empty = 0
    player = 1
    enemy = -1


class BoardMode(IntEnum):
    x3 = 3
    x4 = 4
    x5 = 5


class TicTacToeOnline:
    def __init__(
        self,
        bot: AsteroidBot,
        message: ComponentMessage,
        ctx: SlashContext,
        member: Member,
        content: dict,
        board_mode: BoardMode,
    ) -> None:
        self.bot = bot
        self.message = message
        self.ctx = ctx
        self.member = member
        self.content = content
        self.board_mode = board_mode
        self.board: List[list] = deepcopy(board_template[board_mode])
        self.emoji_circle = self.bot.get_emoji(850792047698509826)
        self.emoji_cross = self.bot.get_emoji(850792048080060456)

    async def start_game(self):
        await self.message.edit(
            content=self.content["GAME_NAME"], components=self.render_gameboard()
        )

        player_1_move = True
        result = False
        while not result:
            if player_1_move:
                result = await self.move(GameState.player, self.member)
                player_1_move = False
            elif not player_1_move:
                result = await self.move(GameState.enemy, self.ctx.author)
                player_1_move = True

    def render_gameboard(self, disable: bool = False):
        components = []
        for i in range(self.board_mode):
            components.insert(i, [])
            for x in range(self.board_mode):
                if self.board[i][x] == GameState.empty:
                    style = ButtonStyle.gray
                    emoji = None
                elif self.board[i][x] == GameState.enemy:
                    style = ButtonStyle.red
                    emoji = self.emoji_circle
                else:
                    style = ButtonStyle.green
                    emoji = self.emoji_cross
                components[i].insert(
                    x,
                    Button(
                        label=" " if not emoji else "",
                        emoji=emoji,
                        style=style,
                        custom_id=f"{i} {x}",
                        disabled=disable if disable else style != ButtonStyle.gray,
                    ),
                )

        return components

    def update_board(self, components: List[List[Button]]):
        for i in range(self.board_mode):
            for j in range(self.board_mode):
                if components[i][j].style == ButtonStyle.gray:
                    self.board[i][j] = GameState.empty
                elif components[i][j].style == ButtonStyle.green:
                    self.board[i][j] = GameState.player
                elif components[i][j].style == ButtonStyle.red:
                    self.board[i][j] = GameState.enemy

    def _check(self, player_id, interaction):
        return (
            interaction.author_id == player_id
            and interaction.message.id == self.message.id
        )

    async def move(self, player: GameState, player_user: Member):
        ctx: ComponentContext = await self.bot.wait_for(
            "button_click",
            check=lambda interaction: self._check(player_user.id, interaction),
        )
        await ctx.defer(edit_origin=True)

        pos = list(map(int, ctx.custom_id.split()))
        self.update_board(ctx.origin_message.components)
        self.board[pos[0]][pos[1]] = player

        await ctx.edit_origin(components=self.render_gameboard())

        if self.is_won(player):
            await self.pick_a_winner(player_user.display_name)
            return True
        if self.is_tie(player):
            return True
        return False

    def is_won(self, player: GameState):
        if self.board_mode == BoardMode.x3:
            win_states = self.get_win_states_x3()
        elif self.board_mode == BoardMode.x4:
            win_states = self.get_win_states_x4()
        elif self.board_mode == BoardMode.x5:
            win_states = self.get_win_states_x5()
        if [player, player, player] in win_states:
            return True
        return False

    def get_win_states_x3(self):
        return [
            [self.board[0][0], self.board[0][1], self.board[0][2]],
            [self.board[1][0], self.board[1][1], self.board[1][2]],
            [self.board[2][0], self.board[2][1], self.board[2][2]],
            [self.board[0][0], self.board[1][0], self.board[2][0]],
            [self.board[0][1], self.board[1][1], self.board[2][1]],
            [self.board[0][2], self.board[1][2], self.board[2][2]],
            [self.board[0][0], self.board[1][1], self.board[2][2]],
            [self.board[0][2], self.board[1][1], self.board[2][0]],
        ]

    def get_win_states_x4(self):
        return [
            [self.board[0][0], self.board[0][1], self.board[0][2]],
            [self.board[0][1], self.board[0][2], self.board[0][3]],
            [self.board[1][0], self.board[1][1], self.board[1][2]],
            [self.board[1][1], self.board[1][2], self.board[1][3]],
            [self.board[2][0], self.board[2][1], self.board[2][2]],
            [self.board[2][1], self.board[2][2], self.board[2][3]],
            [self.board[3][0], self.board[3][1], self.board[3][2]],
            [self.board[3][1], self.board[3][2], self.board[3][3]],
            [self.board[0][0], self.board[1][0], self.board[2][0]],
            [self.board[1][0], self.board[2][0], self.board[3][0]],
            [self.board[0][1], self.board[1][1], self.board[2][1]],
            [self.board[1][1], self.board[2][1], self.board[3][1]],
            [self.board[0][2], self.board[1][2], self.board[2][2]],
            [self.board[1][2], self.board[2][2], self.board[3][2]],
            [self.board[0][3], self.board[1][3], self.board[2][3]],
            [self.board[1][3], self.board[2][3], self.board[3][3]],
            [self.board[0][0], self.board[1][1], self.board[2][2]],
            [self.board[0][1], self.board[1][2], self.board[2][3]],
            [self.board[0][2], self.board[1][1], self.board[2][0]],
            [self.board[0][3], self.board[1][2], self.board[2][1]],
            [self.board[1][3], self.board[2][2], self.board[3][1]],
            [self.board[1][0], self.board[2][1], self.board[3][2]],
        ]

    def get_win_states_x5(self):
        return [
            [self.board[0][0], self.board[0][1], self.board[0][2]],
            [self.board[0][1], self.board[0][2], self.board[0][3]],
            [self.board[0][2], self.board[0][3], self.board[0][4]],
            [self.board[1][0], self.board[1][1], self.board[1][2]],
            [self.board[1][1], self.board[1][2], self.board[1][3]],
            [self.board[1][2], self.board[1][3], self.board[1][4]],
            [self.board[2][0], self.board[2][1], self.board[2][2]],
            [self.board[2][1], self.board[2][2], self.board[2][3]],
            [self.board[2][2], self.board[2][3], self.board[2][4]],
            [self.board[3][0], self.board[3][1], self.board[3][2]],
            [self.board[3][1], self.board[3][2], self.board[3][3]],
            [self.board[3][2], self.board[3][3], self.board[3][4]],
            [self.board[4][0], self.board[4][1], self.board[4][2]],
            [self.board[4][1], self.board[4][2], self.board[4][3]],
            [self.board[4][2], self.board[4][3], self.board[4][4]],
            [self.board[0][0], self.board[1][0], self.board[2][0]],
            [self.board[1][0], self.board[2][0], self.board[3][0]],
            [self.board[2][0], self.board[3][0], self.board[4][0]],
            [self.board[0][1], self.board[1][1], self.board[2][1]],
            [self.board[1][1], self.board[2][1], self.board[3][1]],
            [self.board[2][1], self.board[3][1], self.board[4][1]],
            [self.board[0][2], self.board[1][2], self.board[2][2]],
            [self.board[1][2], self.board[2][2], self.board[3][2]],
            [self.board[2][2], self.board[3][2], self.board[4][2]],
            [self.board[0][3], self.board[1][3], self.board[2][3]],
            [self.board[1][3], self.board[2][3], self.board[3][3]],
            [self.board[2][3], self.board[3][3], self.board[4][3]],
            [self.board[0][4], self.board[1][4], self.board[2][4]],
            [self.board[1][4], self.board[2][4], self.board[3][4]],
            [self.board[2][4], self.board[3][4], self.board[4][4]],
            [self.board[2][0], self.board[1][1], self.board[0][2]],
            [self.board[3][0], self.board[2][1], self.board[1][2]],
            [self.board[2][1], self.board[1][2], self.board[0][3]],
            [self.board[4][0], self.board[3][1], self.board[2][2]],
            [self.board[3][1], self.board[2][2], self.board[1][3]],
            [self.board[2][2], self.board[1][3], self.board[0][4]],
            [self.board[3][1], self.board[3][2], self.board[2][3]],
            [self.board[3][2], self.board[2][3], self.board[1][3]],
            [self.board[4][2], self.board[3][3], self.board[2][4]],
            [self.board[0][2], self.board[1][3], self.board[2][4]],
            [self.board[0][1], self.board[1][2], self.board[2][3]],
            [self.board[1][2], self.board[2][3], self.board[3][4]],
            [self.board[0][0], self.board[1][1], self.board[2][2]],
            [self.board[1][1], self.board[2][2], self.board[3][3]],
            [self.board[2][2], self.board[3][3], self.board[4][4]],
            [self.board[1][0], self.board[2][1], self.board[3][2]],
            [self.board[2][3], self.board[3][3], self.board[4][3]],
            [self.board[2][0], self.board[3][1], self.board[4][2]],
        ]

    def is_tie(self, player: GameState):
        return str(GameState.empty) not in str(self.board) and not self.is_won(player)

    async def pick_a_winner(self, winner="_draw"):
        if winner == "_draw":
            winner = self.content["RESULTS_TIE"]

        embed = Embed(
            title=self.content["RESULTS_TITLE"],
            color=self.bot.get_embed_color(self.ctx.guild_id),
        )
        embed.add_field(
            name=self.content["RESULTS_GAME_NAME"],
            value=self.content["RESULTS_TEXT"].format(
                player1=self.member.display_name,
                player2=self.ctx.author.display_name,
                winner=winner,
            ),
        )

        await self.message.edit(
            embed=embed, components=self.render_gameboard(disable=True)
        )
