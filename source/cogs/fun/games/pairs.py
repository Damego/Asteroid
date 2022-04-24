import asyncio
import contextlib
from random import shuffle

from discord import Forbidden, HTTPException
from discord_slash import Button, ButtonStyle, ComponentContext, SlashContext
from utils import AsteroidBot

from .game_utils import spread_to_rows

all_cards = [
    "🇦🇨",
    "🇦🇩",
    "🇦🇪",
    "🇦🇫",
    "🇦🇬",
    "🇦🇮",
    "🇦🇱",
    "🇦🇲",
    "🇦🇴",
    "🇦🇶",
    "🇦🇷",
    "🇦🇸",
    "🇦🇹",
    "🇦🇺",
    "🇦🇼",
    "🇦🇽",
    "🇦🇿",
    "🇧🇦",
    "🇧🇧",
    "🇧🇩",
    "🇧🇪",
    "🇧🇫",
    "🇧🇬",
    "🇧🇭",
    "🇧🇮",
    "🇧🇯",
    "🇧🇱",
    "🇧🇲",
    "🇧🇳",
    "🇧🇴",
    "🇧🇶",
    "🇧🇷",
    "🇧🇸",
    "🇧🇹",
    "🇧🇻",
    "🇧🇼",
    "🇧🇾",
    "🇧🇿",
    "🇨🇦",
    "🇨🇨",
    "🇨🇩",
    "🇨🇫",
    "🇨🇬",
    "🇨🇭",
    "🇨🇮",
    "🇨🇰",
    "🇨🇱",
    "🇨🇲",
    "🇨🇳",
    "🇨🇴",
    "🇨🇵",
    "🇨🇷",
    "🇨🇺",
    "🇨🇻",
    "🇨🇼",
    "🇨🇽",
    "🇨🇾",
    "🇨🇿",
    "🇩🇪",
    "🇩🇬",
    "🇩🇯",
    "🇩🇰",
    "🇩🇲",
    "🇩🇴",
    "🇩🇿",
    "🇪🇦",
    "🇪🇨",
    "🇪🇪",
    "🇪🇬",
    "🇪🇭",
    "🇪🇷",
    "🇪🇸",
    "🇪🇹",
    "🇪🇺",
    "🇫🇮",
    "🇫🇯",
    "🇫🇰",
    "🇫🇲",
    "🇫🇴",
    "🇫🇷",
    "🇬🇦",
    "🇬🇧",
    "🇬🇩",
    "🇬🇪",
    "🇬🇫",
    "🇬🇬",
    "🇬🇭",
    "🇬🇮",
    "🇬🇱",
    "🇬🇲",
    "🇬🇳",
    "🇬🇵",
    "🇬🇶",
    "🇬🇷",
    "🇬🇸",
    "🇬🇹",
    "🇬🇺",
    "🇬🇼",
    "🇬🇾",
    "🇭🇰",
    "🇭🇲",
    "🇭🇳",
    "🇭🇷",
    "🇭🇹",
    "🇭🇺",
    "🇮🇨",
    "🇮🇩",
    "🇮🇪",
    "🇮🇱",
    "🇮🇲",
    "🇮🇳",
    "🇮🇴",
    "🇮🇶",
    "🇮🇷",
    "🇮🇸",
    "🇮🇹",
    "🇯🇪",
    "🇯🇲",
    "🇯🇴",
    "🇯🇵",
    "🇰🇪",
    "🇰🇬",
    "🇰🇭",
    "🇰🇮",
    "🇰🇲",
    "🇰🇳",
    "🇰🇵",
    "🇰🇷",
    "🇰🇼",
    "🇰🇾",
    "🇰🇿",
    "🇱🇦",
    "🇱🇧",
    "🇱🇨",
    "🇱🇮",
    "🇱🇰",
    "🇱🇷",
    "🇱🇸",
    "🇱🇹",
    "🇱🇺",
    "🇱🇻",
    "🇱🇾",
    "🇲🇦",
    "🇲🇨",
    "🇲🇩",
    "🇲🇪",
    "🇲🇫",
    "🇲🇬",
    "🇲🇭",
    "🇲🇰",
    "🇲🇱",
    "🇲🇲",
    "🇲🇳",
    "🇲🇴",
    "🇲🇵",
    "🇲🇶",
    "🇲🇷",
    "🇲🇸",
    "🇲🇹",
    "🇲🇺",
    "🇲🇻",
    "🇲🇼",
    "🇲🇽",
    "🇲🇾",
    "🇲🇿",
    "🇳🇦",
    "🇳🇨",
    "🇳🇪",
    "🇳🇫",
    "🇳🇬",
    "🇳🇮",
    "🇳🇱",
    "🇳🇴",
    "🇳🇵",
    "🇳🇷",
    "🇳🇺",
    "🇳🇿",
    "🇴🇲",
    "🇵🇦",
    "🇵🇪",
    "🇵🇫",
    "🇵🇬",
    "🇵🇭",
    "🇵🇰",
    "🇵🇱",
    "🇵🇲",
    "🇵🇳",
    "🇵🇷",
    "🇵🇸",
    "🇵🇹",
    "🇵🇼",
    "🇵🇾",
    "🇶🇦",
    "🇷🇪",
    "🇷🇴",
    "🇷🇸",
    "🇷🇺",
    "🇷🇼",
    "🇸🇦",
    "🇸🇧",
    "🇸🇨",
    "🇸🇩",
    "🇸🇪",
    "🇸🇬",
    "🇸🇭",
    "🇸🇮",
    "🇸🇯",
    "🇸🇰",
    "🇸🇱",
    "🇸🇲",
    "🇸🇳",
    "🇸🇴",
    "🇸🇷",
    "🇸🇸",
    "🇸🇹",
    "🇸🇻",
    "🇸🇽",
    "🇸🇾",
    "🇸🇿",
    "🇹🇦",
    "🇹🇨",
    "🇹🇩",
    "🇹🇫",
    "🇹🇬",
    "🇹🇭",
    "🇹🇯",
    "🇹🇰",
    "🇹🇱",
    "🇹🇲",
    "🇹🇳",
    "🇹🇴",
    "🇹🇷",
    "🇹🇹",
    "🇹🇻",
    "🇹🇼",
    "🇹🇿",
    "🇺🇦",
    "🇺🇬",
    "🇺🇲",
    "🇺🇳",
    "🇺🇸",
    "🇺🇾",
    "🇺🇿",
    "🇻🇦",
    "🇻🇨",
    "🇻🇪",
    "🇻🇬",
    "🇻🇮",
    "🇻🇳",
    "🇻🇺",
    "🇼🇫",
    "🇼🇸",
    "🇽🇰",
    "🇾🇪",
    "🇾🇹",
    "🇿🇦",
    "🇿🇲",
    "🇿🇼",
]


class Pairs:
    def __init__(self, ctx: SlashContext) -> None:
        self.ctx = ctx
        self.bot: AsteroidBot = ctx.bot
        cards = all_cards.copy()
        shuffle(cards)
        shuffle(cards)
        self.cards = cards[:12] * 2
        self.first_card = self.second_card = self.first_card_ind = self.second_card_ind = None
        self.attempts = 0
        self.base_message = f"Collect a pairs! Attempts: `{self.attempts}`"

    def _render_start_components(self):
        components = [Button(label=" ", custom_id=f"pairs|{ind}") for ind in range(24)]
        components.append(Button(label="❌", style=ButtonStyle.blue, custom_id="pairs|close"))
        self.raw_components = components
        return spread_to_rows(components)

    def is_equal(self):
        if self.first_card == self.second_card:
            self.raw_components[self.first_card_ind].style = ButtonStyle.green
            self.raw_components[self.second_card_ind].style = ButtonStyle.green
            self.first_card = self.second_card = self.first_card_ind = self.second_card_ind = None
            return True
        else:
            self.raw_components[self.first_card_ind].label = " "
            self.raw_components[self.first_card_ind].emoji = None
            self.raw_components[self.first_card_ind].disabled = False
            self.raw_components[self.second_card_ind].label = " "
            self.raw_components[self.second_card_ind].emoji = None
            self.raw_components[self.second_card_ind].disabled = False

            self.first_card = self.second_card = self.first_card_ind = self.second_card_ind = None
            return False

    def is_won(self):
        for component in self.raw_components:
            if component.style == ButtonStyle.gray:
                return

        self.raw_components[-1].disabled = True
        self.base_message = f"You won! Attempts: `{self.attempts}`"

    async def start(self):
        self.message = await self.ctx.send(
            self.base_message, components=self._render_start_components()
        )

        while True:
            ctx = await self._wait_button_click()
            if not ctx:
                return
            _, ind = ctx.custom_id.split("|")
            if ind == "close":
                return await ctx.edit_origin(components=self._disable_components())
            ind = int(ind)
            self.attempts += 1

            if self.first_card is None:
                self.first_card = self.cards[ind]
                self.first_card_ind = ind
                self.raw_components[ind].emoji = self.cards[self.first_card_ind]
                self.raw_components[self.first_card_ind].label = None
                self.raw_components[self.first_card_ind].disabled = True
            elif self.second_card is None:
                self.second_card = self.cards[ind]
                self.second_card_ind = ind
                self.raw_components[self.second_card_ind].emoji = self.cards[self.second_card_ind]
                self.raw_components[self.second_card_ind].label = None
                self.raw_components[self.second_card_ind].disabled = True

            await ctx.edit_origin(
                content=self.base_message, components=spread_to_rows(self.raw_components)
            )
            if self.first_card is not None and self.second_card is not None:
                if not self.is_equal():
                    await asyncio.sleep(0.5)
                else:
                    self.is_won()
                await ctx.origin_message.edit(
                    self.base_message, components=spread_to_rows(self.raw_components)
                )

    async def _wait_button_click(self) -> ComponentContext:
        def check(ctx: ComponentContext):
            return ctx.author_id == self.ctx.author_id and ctx.origin_message_id == self.message.id

        try:
            ctx = await self.bot.wait_for("button_click", timeout=120, check=check)
        except asyncio.TimeoutError:
            with contextlib.suppress(Forbidden, HTTPException):
                return await self.message.edit(
                    content=f"Timed out. Attempts: `{self.attempts}`",
                    components=self._disable_components(),
                )
        return ctx

    def _disable_components(self):
        for component in self.raw_components:
            if component.style == ButtonStyle.green:
                continue
            _, ind = component.custom_id.split("|")
            if ind != "close":
                component.style = ButtonStyle.red
                component.emoji = self.cards[int(ind)]
                component.label = None
            component.disabled = True

        return spread_to_rows(self.raw_components)
