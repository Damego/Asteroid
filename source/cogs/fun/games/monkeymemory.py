import asyncio
from copy import copy
from random import shuffle
from uuid import uuid1

from discord_slash import Button, ButtonStyle, ComponentContext, SlashContext
from utils import AsteroidBot

from .game_utils import spread_to_rows

template = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

emoji = {
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
}


class MonkeyMemory:
    def __init__(self, ctx: SlashContext, timeout: int) -> None:
        self.bot: AsteroidBot = ctx.bot
        self.ctx = ctx
        self.board = copy(template)
        self.timeout = timeout

        shuffle(self.board)

    def _render_start_components(self):
        raw_components = []
        for num in self.board:
            if num == 0:
                raw_components.append(
                    Button(
                        label=" ",
                        style=ButtonStyle.gray,
                        disabled=True,
                        custom_id=f"mm|empty{uuid1()}",
                    )
                )
            else:
                raw_components.append(
                    Button(
                        emoji=emoji[str(num)],
                        style=ButtonStyle.gray,
                        custom_id=f"mm|{num}",
                        disabled=True,
                    )
                )
        self.components = spread_to_rows(raw_components)
        return self.components

    def toggle_components_status(self, *, hide: bool):
        for row in self.components:
            for component in row:
                if hide:
                    if component.emoji is not None:
                        component.emoji = None
                        component.label = " "
                    component.disabled = False
                else:
                    _, _id = component.custom_id.split("|")
                    if not _id.startswith("empty"):
                        component.emoji = emoji[_id]
                        component.label = None
        return self.components

    def _disable_components(self):
        for row in self.components:
            row.disable_components()

        return self.components

    def paint_button(self, button_id: str, style: ButtonStyle):
        for row in self.components:
            for component in row:
                _, _id = component.custom_id.split("|")
                if _id != button_id:
                    continue
                if emoji.get(_id):
                    component.emoji = emoji[_id]
                    component.label = None
                component.style = style
                component.disabled = True

    async def _wait_button_click(self) -> ComponentContext:
        def check(ctx: ComponentContext):
            return ctx.author_id == self.ctx.author_id and ctx.origin_message_id == self.message.id

        try:
            ctx = await self.bot.wait_for("button_click", timeout=600, check=check)
        except asyncio.TimeoutError:
            await self.message.edit(content="Timed out", components=self._disable_components())
        else:
            return ctx

    async def start(self):
        self.message = await self.ctx.send(
            f"You have `{self.timeout}` seconds to remember the sequence.",
            components=self._render_start_components(),
        )
        current = 1
        is_end = False

        await asyncio.sleep(self.timeout)
        await self.message.edit(
            content="Monkey Memory", components=self.toggle_components_status(hide=True)
        )

        while True:
            ctx = await self._wait_button_click()
            if not ctx:
                return

            _, num = ctx.custom_id.split("|")
            if not num.startswith("empty") and int(num) == current:
                current += 1
                self.paint_button(num, ButtonStyle.green)
            else:
                self.paint_button(num, ButtonStyle.red)
                self._disable_components()
                self.toggle_components_status(hide=False)
                is_end = True
            if current == 10:
                self._disable_components()

            await ctx.edit_origin(components=self.components)
            if is_end:
                return
