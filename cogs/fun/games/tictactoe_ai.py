"""
Origin code for minimax ai was taken from https://github.com/goverfl0w/slash-bot/blob/master/cogs/games/tictactoe.py
"""
from asyncio import TimeoutError, to_thread
from copy import deepcopy
from datetime import datetime
from enum import IntEnum
from random import choice
from math import inf
from typing import List

from discord import Embed
from discord_slash import (
    ComponentContext,
    ComponentMessage,
    Button,
    ButtonStyle,
)


from utils import AsteroidBot


BoardTemplate = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


class GameState(IntEnum):
    empty = 0
    player = -1
    ai = +1


class TicTacToeMode(IntEnum):
    easy = 2
    impossible = 4


class TicTacToeAI:
    def __init__(
        self,
        bot: AsteroidBot,
        ctx: ComponentContext,
        mode: TicTacToeMode,
    ):
        self.bot = bot
        self.ctx = ctx
        self.difficult = "Easy" if mode == 2 else "Impossible"
        self.mode = mode
        self.board: List[list] = None
        self.emoji_circle = self.bot.get_emoji(850792047698509826)
        self.emoji_cross = self.bot.get_emoji(850792048080060456)
        self.game_embed = None

    def is_won(self, board: List[list], player: GameState):
        win_states = [
            [board[0][0], board[0][1], board[0][2]],
            [board[1][0], board[1][1], board[1][2]],
            [board[2][0], board[2][1], board[2][2]],
            [board[0][0], board[1][0], board[2][0]],
            [board[0][1], board[1][1], board[2][1]],
            [board[0][2], board[1][2], board[2][2]],
            [board[0][0], board[1][1], board[2][2]],
            [board[2][0], board[1][1], board[0][2]],
        ]
        if [player, player, player] in win_states:
            return True
        return False

    def evaluate(self, board: List[list]):
        if self.is_won(board, GameState.player):
            return -1
        if self.is_won(board, GameState.ai):
            return +1
        return 0

    def get_possible_moves(self, board: List[list]):
        possible_moves = []
        for i in range(3):
            for x in range(3):
                if board[i][x] == GameState.empty:
                    possible_moves.append([i, x])
        return possible_moves

    def minimax(self, board: List[list], depth: int, player: GameState):
        best = [-1, -1, -inf] if player == GameState.ai else [-1, -1, +inf]
        if (
            depth == 0
            or self.is_won(board, GameState.player)
            or self.is_won(board, GameState.ai)
        ):
            score = self.evaluate(board)
            return [-1, -1, score]

        for move in self.get_possible_moves(board):
            x, y = move[0], move[1]
            board[x][y] = player
            score = self.minimax(board, depth - 1, -player)
            board[x][y] = GameState.empty
            score[0], score[1] = x, y

            if (
                player == GameState.ai
                and score[2] > best[2]
                or player != GameState.ai
                and score[2] < best[2]
            ):
                best = score
        return best

    def render_gameboard(self, disable: bool = False):
        if self.board is None:
            self.board = deepcopy(BoardTemplate)

        components = []
        for i in range(3):
            components.insert(i, [])
            for x in range(3):
                if self.board[i][x] == GameState.empty:
                    style = ButtonStyle.gray
                    emoji = None
                elif self.board[i][x] == GameState.ai:
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
                        disabled=disable or style != ButtonStyle.gray,
                    ),
                )

        return components

    def get_board_state(self, components: List[List[Button]]):
        board = deepcopy(BoardTemplate)
        for i in range(3):
            for j in range(3):
                if components[i][j].style == ButtonStyle.gray:
                    board[i][j] = GameState.empty
                elif components[i][j].style == ButtonStyle.green:
                    board[i][j] = GameState.player
                elif components[i][j].style == ButtonStyle.red:
                    board[i][j] = GameState.ai
        return board

    async def process_minimax(self):
        depth = len(self.get_possible_moves(self.board))
        if depth != 0:
            ai_move = await to_thread(
                self.minimax, deepcopy(self.board), depth, GameState.ai
            )
            return ai_move

    async def process_turn(self, ctx: ComponentContext):
        await ctx.defer(edit_origin=True)
        pos = list(map(int, ctx.custom_id.split()))
        self.board = self.get_board_state(ctx.origin_message.components)
        self.board[pos[0]][pos[1]] = GameState.player

        if not self.is_won(self.board, GameState.player):
            moves = self.get_possible_moves(self.board)
            if len(moves) != 0:
                if self.mode == TicTacToeMode.easy:
                    ai_move = choice(moves)
                else:
                    ai_move = await self.process_minimax()
                x, y = ai_move[0], ai_move[1]
                self.board[x][y] = GameState.ai

        if self.is_won(self.board, GameState.player):
            winner = ctx.author.mention
        elif self.is_won(self.board, GameState.ai):
            winner = ctx.bot.user.mention
        elif len(self.get_possible_moves(self.board)) == 0:
            winner = "Draw"
        else:
            winner = None

        if winner:
            self.game_embed.description += f"\n**Winner:** {winner}"

        await ctx.edit_origin(embed=self.game_embed, components=self.render_gameboard())
        return winner is not None

    async def start(
        self,
        *,
        edit_origin: bool = False,
        message: ComponentMessage = None,
    ):
        ctx = self.ctx
        self.game_embed = Embed(
            title="Tic Tac Toe Game",
            description=f"**Player:** {ctx.author.mention}"
            f"\n**Difficult:** `{self.difficult}`",
            color=await self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow(),
        )
        self.game_embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        if not edit_origin:
            message = await ctx.send(
                embed=self.game_embed, components=self.render_gameboard()
            )
        else:
            await ctx.edit_origin(
                embed=self.game_embed, components=self.render_gameboard()
            )

        while True:
            try:
                comp_ctx: ComponentContext = await self.bot.wait_for(
                    "button_click",
                    check=lambda _ctx: ctx.author_id == _ctx.author_id
                    and message.id == _ctx.origin_message.id,
                    timeout=180,
                )
            except TimeoutError:
                components = self.render_gameboard(disable=True)
                return await ctx.origin_message.edit(components=components)

            res = await self.process_turn(comp_ctx)
            if res:
                components = self.render_gameboard(disable=True)
                return await comp_ctx.origin_message.edit(components=components)
