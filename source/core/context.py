from typing import TYPE_CHECKING

import interactions
from interactions.client import context

if TYPE_CHECKING:
    from core import Asteroid


# Cursed stuff. Made for fun. Nothing more
class Endl:
    ...


endl = Endl()


class CursedValues:
    def __init__(self, ctx: context._Context):
        self.ctx = ctx
        self.content: str = interactions.MISSING
        self.embeds: list[interactions.Embed] = interactions.MISSING
        self.components: list[
            interactions.Button | interactions.SelectMenu | interactions.ActionRow
        ] = interactions.MISSING
        self.ephemeral: bool = interactions.MISSING

    def __lshift__(self, other):
        if isinstance(other, Endl):
            self.ctx.client._loop.create_task(
                self.ctx.send(
                    self.content,
                    embeds=self.embeds,
                    components=self.components,
                    ephemeral=bool(self.ephemeral),
                )
            )
            return

        if isinstance(other, str):
            self.content = other
        elif isinstance(other, interactions.Embed):
            self.embeds = [other]
        elif isinstance(
            other, (interactions.Button, interactions.SelectMenu, interactions.ActionRow)
        ):
            self.components = [other]
        elif isinstance(other, list):
            first = other[0]
            if isinstance(first, interactions.Embed):
                self.embeds = other
            elif isinstance(
                first, (interactions.Button, interactions.SelectMenu, interactions.ActionRow)
            ):
                self.components = other
        elif isinstance(other, dict):
            self.ephemeral = other.get("ephemeral", interactions.MISSING)

        return self


class CursedContext(context._Context):
    async def __get_cursed(self):
        return CursedValues(self)

    def __await__(self):
        return self.__get_cursed().__await__()


class CustomContext(CursedContext):
    def translate(self, key: str, *args, **kwargs) -> str:
        client: "Asteroid" = self.client  # type: ignore
        return client.i18n.get_translate(key, self.locale).format(*args, **kwargs)


class CommandContext(context.CommandContext, CustomContext):
    ...


class ComponentContext(context.ComponentContext, CustomContext):
    ...
