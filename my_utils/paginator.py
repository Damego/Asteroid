from copy import deepcopy
from enum import IntEnum
from typing import Union, List

from discord import Client, Embed
from discord.ext.commands import Bot
from discord_slash import SlashContext, Button, ButtonStyle, ComponentContext, ComponentMessage


components = {
    1: [
        [
            Button(style=ButtonStyle.gray, label="←", custom_id="back", disabled=True),
            Button(style=ButtonStyle.gray, label="→", custom_id="next"),
        ]
    ],
    2: [
        [
            Button(style=ButtonStyle.gray, label="<<", custom_id="first", disabled=True),
            Button(style=ButtonStyle.gray, label="←", custom_id="back", disabled=True),
            Button(style=ButtonStyle.gray, label="→", custom_id="next"),
            Button(style=ButtonStyle.gray, label=">>", custom_id="last"),
        ]
    ],
    3: [
        [
            Button(style=ButtonStyle.gray, label="←", custom_id="back", disabled=True),
            Button(
                style=ButtonStyle.green,
                label="1/{pages}",
                emoji="🏠",
                custom_id="home",
                disabled=True,
            ),
            Button(style=ButtonStyle.gray, label="→", custom_id="next"),
        ]
    ],
    4: [
        [
            Button(style=ButtonStyle.gray, label="<<", custom_id="first", disabled=True),
            Button(style=ButtonStyle.gray, label="←", custom_id="back", disabled=True),
            Button(style=ButtonStyle.blue, label="1/{pages}", disabled=True),
            Button(style=ButtonStyle.gray, label="→", custom_id="next"),
            Button(style=ButtonStyle.gray, label=">>", custom_id="last"),
        ]
    ],
}


class PaginatorStyle(IntEnum):
    TWO_BUTTONS = 1
    FOUR_BUTTONS = 2
    THREE_BUTTONS_WITH_COUNT = 3
    FIVE_BUTTONS_WITH_COUNT = 4


class Paginator:
    def __init__(
        self,
        bot: Union[Client, Bot],
        ctx: SlashContext,
        style: int,
        embeds: List[Embed],
    ) -> None:
        self.bot = bot
        self.ctx = ctx
        self.style = style
        self.components = deepcopy(components[self.style])
        self.embeds = embeds
        self.pages = len(embeds)
        self.current_page = 1
        self.message = None
        self.button_ctx = None

        if self.style == 3:
            self.components[0][1].label = f"1/{self.pages}"
        elif self.style == 4:
            self.components[0][2].label = f"1/{self.pages}"

    async def start(self):
        self.message: ComponentMessage = await self.ctx.send(
            embed=self.embeds[0], components=self.components
        )

        self.bot.add_listener(self.button_click, "on_button_click")

    async def button_click(self, ctx: ComponentContext):
        if ctx.author_id != self.ctx.author_id or ctx.origin_message_id != self.message.id:
            return

        if self.style == 1:
            self._process_style1(ctx.custom_id)
        elif self.style == 2:
            self._process_style2(ctx.custom_id)
        elif self.style == 3:
            self._process_style3(ctx.custom_id)
        elif self.style == 4:
            self._process_style4(ctx.custom_id)

        print(self.components[0][0].to_dict())
        print(self.components[0][1].to_dict())

        await ctx.edit_origin(
            embed=self.embeds[self.current_page - 1], components=self.components
        )

    def _process_style1(self, custom_id: str):
        if custom_id == "back":
            if self.current_page == self.pages:
                self.components[0][-1].disabled = False
            self.current_page -= 1
            if self.current_page == 1:
                self.components[0][0].disabled = True
            elif self.current_page == 2:
                self.components[0][0].disabled = False
        elif custom_id == "next":
            if self.current_page == 1:
                self.components[0][0].disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                self.components[0][-1].disabled = True
            elif self.current_page == self.pages - 1:
                self.components[0][-1].disabled = False

    def _process_style2(self, custom_id: str):
        first_button = self.components[0][0]
        second_button = self.components[0][1]
        second_last_button = self.components[0][-2]
        last_button = self.components[0][-1]

        if custom_id == "back":
            if self.current_page == self.pages:
                second_last_button.disabled = False
                last_button.disabled = False
            self.current_page -= 1
            if self.current_page == 1:
                first_button.disabled = True
                second_button.disabled = True
            elif self.current_page == 2:
                first_button.disabled = False
                second_button.disabled = False

        elif custom_id == "first":
            self.current_page = 1
            first_button.disabled = True
            second_button.disabled = True
            second_last_button.disabled = False
            last_button.disabled = False

        elif custom_id == "last":
            self.current_page = self.pages
            first_button.disabled = False
            second_button.disabled = False
            second_last_button.disabled = True
            last_button.disabled = True

        elif custom_id == "next":
            if self.current_page == 1:
                first_button.disabled = False
                second_button.disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                second_last_button.disabled = True
                last_button.disabled = True
            elif self.current_page == self.pages - 1:
                second_last_button.disabled = False
                last_button.disabled = False

    def _process_style3(self, custom_id: str):
        if custom_id == "back":
            if self.current_page == self.pages:
                self.components[0][-1].disabled = False
            self.current_page -= 1
            if self.current_page == 1:
                self.components[0][0].disabled = True
                self.components[0][1].disabled = True
            elif self.current_page == 2:
                self.components[0][0].disabled = False
        elif custom_id == "home":
            self.current_page = 1
            self.components[0][0].disabled = True
            self.components[0][1].disabled = True
        elif custom_id == "next":
            if self.current_page == 1:
                self.components[0][0].disabled = False
                self.components[0][1].disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                self.components[0][-1].disabled = True
            elif self.current_page == self.pages - 1:
                self.components[0][-1].disabled = False

        self.components[0][1].label = f"{self.current_page}/{self.pages}"

    def _process_style4(self, custom_id: str):
        first_button = self.components[0][0]
        second_button = self.components[0][1]
        second_last_button = self.components[0][-2]
        last_button = self.components[0][-1]
        pages_button = self.components[0][2]

        if custom_id == "back":
            if self.current_page == self.pages:
                second_last_button.disabled = False
                last_button.disabled = False
            self.current_page -= 1
            if self.current_page == 1:
                first_button.disabled = True
                second_button.disabled = True
            elif self.current_page == 2:
                first_button.disabled = False
                second_button.disabled = False

        elif custom_id == "first":
            self.current_page = 1
            first_button.disabled = True
            second_button.disabled = True
            second_last_button.disabled = False
            last_button.disabled = False

        elif custom_id == "last":
            self.current_page = self.pages
            first_button.disabled = False
            second_button.disabled = False
            second_last_button.disabled = True
            last_button.disabled = True

        elif custom_id == "next":
            if self.current_page == 1:
                first_button.disabled = False
                second_button.disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                second_last_button.disabled = True
                last_button.disabled = True
            elif self.current_page == self.pages - 1:
                second_last_button.disabled = False
                last_button.disabled = False

        pages_button.label = f"{self.current_page}/{self.pages}"
