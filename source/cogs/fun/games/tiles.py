from asyncio import TimeoutError
from copy import copy
from random import shuffle

from discord_slash import Button, ButtonStyle, ComponentContext, SlashContext
from utils import AsteroidBot

from .game_utils import spread_to_rows

# board_3x3 = list(range(9))
board_4x4 = list(range(16))
# board_5x5 = list(range(25))
# TODO: Implement logic for 3x3 and 5x5


class Tiles:
    def __init__(self, ctx: SlashContext) -> None:
        self.ctx = ctx
        self.bot: AsteroidBot = ctx.bot
        self.board = copy(board_4x4)
        self.message = None
        self.moves = 0

        shuffle(self.board)

    def _render_components(self, *, disabled: bool = False):
        components = [None] * len(self.board)
        for num in self.board:
            i = self.board.index(num)
            if num == 0:
                components[i] = Button(
                    label=" ",
                    style=ButtonStyle.gray,
                    custom_id="tiles|0",
                    disabled=disabled,
                )
            else:
                components[i] = Button(
                    label=f"{num}",
                    style=ButtonStyle.blue,
                    custom_id=f"tiles|{num}",
                    disabled=disabled,
                )
        components = spread_to_rows(components, 4)
        return components

    def _is_won(self):
        for i in range(len(self.board)):
            if self.board[i] == 0 and i < len(self.board):
                continue
            elif self.board[i] != i + 1:
                return False
        return True

    async def start(self):
        def check(ctx: ComponentContext):
            return ctx.author_id == self.ctx.author_id and ctx.origin_message_id == self.message.id

        self.message = await self.ctx.send(
            f"Tiles. Moves: {self.moves}", components=self._render_components()
        )

        while True:
            try:
                ctx: ComponentContext = await self.bot.wait_for(
                    "button_click", check=check, timeout=120
                )
            except TimeoutError:
                await self.message.edit(
                    content=f"Tiles. Moves: {self.moves}",
                    components=self._render_components(disabled=True),
                )
                return

            self.moves += 1
            _, num = ctx.custom_id.split("|")
            index = self.board.index(int(num))

            if index + 1 <= len(self.board) and (index + 1) % 4 != 0 and self.board[index + 1] == 0:
                self.board[index + 1], self.board[index] = (
                    self.board[index],
                    self.board[index + 1],
                )
            elif index - 1 >= 0 and (index - 1) % 4 != 3 and self.board[index - 1] == 0:
                self.board[index - 1], self.board[index] = (
                    self.board[index],
                    self.board[index - 1],
                )
            elif index + 4 < len(self.board) and self.board[index + 4] == 0:
                self.board[index + 4], self.board[index] = (
                    self.board[index],
                    self.board[index + 4],
                )
            elif index - 4 >= 0 and self.board[index - 4] == 0:
                self.board[index - 4], self.board[index] = (
                    self.board[index],
                    self.board[index - 4],
                )
            else:
                self.moves -= 1

            if self._is_won():
                return await ctx.edit_origin(
                    content=f"Tiles. You won! Moves: {self.moves}",
                    components=self._render_components(disabled=True),
                )
            await ctx.edit_origin(
                content=f"Tiles. Moves: {self.moves}",
                components=self._render_components(),
            )
