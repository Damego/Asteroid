from typing import TYPE_CHECKING

import interactions
from interactions.client import context

if TYPE_CHECKING:
    from core import Asteroid


# Cursed stuff. Made for fun. Nothing more
class CursedValues:
    def __init__(self):
        self.content: str = interactions.MISSING
        self.embeds: list[interactions.Embed] = interactions.MISSING
        self.components: list[
            interactions.Button | interactions.SelectMenu | interactions.ActionRow
        ] = interactions.MISSING
        self.ephemeral: bool = interactions.MISSING


class CursedContext(context._Context):
    cursed_values: CursedValues

    def __lshift__(self, other):
        if not hasattr(self, "cursed_values"):
            self.cursed_values = CursedValues()

        if isinstance(other, str):
            self.cursed_values.content = other
        elif isinstance(other, interactions.Embed):
            self.cursed_values.embeds = [other]
        elif isinstance(
            other, (interactions.Button, interactions.SelectMenu, interactions.ActionRow)
        ):
            self.cursed_values.components = [other]
        elif isinstance(other, list):
            first = other[0]
            if isinstance(first, interactions.Embed):
                self.cursed_values.embeds = other
            elif isinstance(
                first, (interactions.Button, interactions.SelectMenu, interactions.ActionRow)
            ):
                self.cursed_values.components = other
        elif isinstance(other, dict):
            self.cursed_values.ephemeral = other.get("ephemeral", interactions.MISSING)

        return self

    def __await__(self):
        if not hasattr(self, "cursed_values"):
            raise Exception("Can't await context without passed params")

        return self.send(
            self.cursed_values.content,
            embeds=self.cursed_values.embeds,
            components=self.cursed_values.components,
            ephemeral=bool(self.cursed_values.ephemeral),
        ).__await__()


class CustomContext(CursedContext):
    def translate(self, key: str, *args, **kwargs) -> str:
        client: "Asteroid" = self.client  # type: ignore
        return client.i18n.get_translate(key, self.locale).format(*args, **kwargs)


class CommandContext(context.CommandContext, CustomContext):
    ...


class ComponentContext(context.ComponentContext, CustomContext):
    ...
