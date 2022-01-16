from asyncio import TimeoutError
from copy import deepcopy
from enum import IntEnum
from typing import Union, List

from discord import Client, Embed
from discord.ext.commands import Bot
from discord_slash import SlashContext
from discord_components import Button, ButtonStyle
from discord_slash_components_bridge import ComponentContext, ComponentMessage


components = {
    1: [
        [
            Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
            Button(style=ButtonStyle.gray, label='→', id='next'),
        ]
    ],
    2: [
            [
                Button(style=ButtonStyle.gray, label='<<', id='first', disabled=True),
                Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
                Button(style=ButtonStyle.gray, label='→', id='next'),
                Button(style=ButtonStyle.gray, label='>>', id='last')
            ]
        ],
    3: [
        [
            Button(
                style=ButtonStyle.gray, label='←', id='back', disabled=True
            ),
            Button(
                style=ButtonStyle.green,
                label='1/{pages}',
                emoji='🏠',
                id='home',
                disabled=True,
            ),
            Button(style=ButtonStyle.gray, label='→', id='next'),
        ]
    ],
    4: [
            [
                Button(style=ButtonStyle.gray, label='<<', id='first', disabled=True),
                Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
                Button(style=ButtonStyle.blue, label='1/{pages}', disabled=True),
                Button(style=ButtonStyle.gray, label='→', id='next'),
                Button(style=ButtonStyle.gray, label='>>', id='last')
            ]
        ]
}


class PaginatorStyle(IntEnum):
    TWO_BUTTONS = 1
    FOUR_BUTTONS = 2
    THREE_BUTTONS_WITH_COUNT = 3
    FIVE_BUTTONS_WITH_COUNT = 4


class Paginator:
    def __init__(self, bot: Union[Client, Bot], ctx: SlashContext, style: int, embeds: List[Embed]) -> None:
        self.bot = bot
        self.ctx = ctx
        self.style = style
        self.components = deepcopy(components[self.style])
        self.embeds = embeds
        self.pages = len(embeds)
        self.current_page = 1
        self.message = None
        self._interaction = None

        if self.style == 3:
            self.components[0][1].label = f'1/{self.pages}'
        elif self.style == 4:
            self.components[0][2].label = f'1/{self.pages}'

    async def start(self):
        self.message: ComponentMessage = await self.ctx.send(embed=self.embeds[0], components=self.components)

        while True:
            self._interaction = await self._get_interaction()
            if self._interaction is None:
                return

            if self.style == 1:
                self._process_style1()
            elif self.style == 2:
                self._process_style2()
            elif self.style == 3:
                self._process_style3()
            elif self.style == 4:
                self._process_style4()

            try:
                await self._interaction.edit_origin(embed=self.embeds[self.current_page-1], components=self.components)
            except Exception as e:
                print(e)

    async def _get_interaction(self) -> ComponentContext:
        try:
            return await self.bot.wait_for(
                'button_click',
                check=lambda ctx: ctx.author_id == self.ctx.author_id and ctx.message.id == self.message.id,
                timeout=60
            )
        except TimeoutError:
            await self.message.edit(components=[])

    def _process_style1(self):
        custom_id = self._interaction.custom_id
        if custom_id == 'back':
            if self.current_page == self.pages:
                self.components[0][-1].disabled = False
            self.current_page -= 1
            if self.current_page == 1:
                self.components[0][0].disabled = True
            elif self.current_page == 2:
                self.components[0][0].disabled = False
        elif custom_id == 'next':
            if self.current_page == 1:
                self.components[0][0].disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                self.components[0][-1].disabled = True
            elif self.current_page == self.pages - 1:
                self.components[0][-1].disabled = False

    def _process_style2(self):
        custom_id = self._interaction.custom_id
        first_button = self.components[0][0]
        second_button = self.components[0][1]
        second_last_button = self.components[0][-2]
        last_button = self.components[0][-1]

        if custom_id == 'back':
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

        elif custom_id == 'first':
            self.current_page = 1
            first_button.disabled = True
            second_button.disabled = True
            second_last_button.disabled = False
            last_button.disabled = False

        elif custom_id == 'last':
            self.current_page = self.pages
            first_button.disabled = False
            second_button.disabled = False
            second_last_button.disabled = True
            last_button.disabled = True

        elif custom_id == 'next':
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

    def _process_style3(self):
        custom_id = self._interaction.custom_id

        if custom_id == 'back':
            if self.current_page == self.pages:
                self.components[0][-1].disabled = False
            self.current_page -= 1
            if self.current_page == 1:
                self.components[0][0].disabled = True
                self.components[0][1].disabled = True
            elif self.current_page == 2:
                self.components[0][0].disabled = False
        elif custom_id == 'home':
            self.current_page = 1
            self.components[0][0].disabled = True
            self.components[0][1].disabled = True
        elif custom_id == 'next':
            if self.current_page == 1:
                self.components[0][0].disabled = False
                self.components[0][1].disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                self.components[0][-1].disabled = True
            elif self.current_page == self.pages-1:
                self.components[0][-1].disabled = False

        self.components[0][1].label = f'{self.current_page}/{self.pages}'

    def _process_style4(self):
        custom_id = self._interaction.custom_id

        first_button = self.components[0][0]
        second_button = self.components[0][1]
        second_last_button = self.components[0][-2]
        last_button = self.components[0][-1]
        pages_button = self.components[0][2]

        if custom_id == 'back':
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

        elif custom_id == 'first':
            self.current_page = 1
            first_button.disabled = True
            second_button.disabled = True
            second_last_button.disabled = False
            last_button.disabled = False

        elif custom_id == 'last':
            self.current_page = self.pages
            first_button.disabled = False
            second_button.disabled = False
            second_last_button.disabled = True
            last_button.disabled = True

        elif custom_id == 'next':
            if self.current_page == 1:
                first_button.disabled = False
                second_button.disabled = False
            self.current_page += 1
            if self.current_page == self.pages:
                second_last_button.disabled = True
                last_button.disabled = True
            elif self.current_page == self.pages-1:
                second_last_button.disabled = False
                last_button.disabled = False

        pages_button.label = f'{self.current_page}/{self.pages}'

