from typing import TYPE_CHECKING

from interactions.client import context

if TYPE_CHECKING:
    from core import Asteroid


class CustomContext(context._Context):
    def translate(self, key: str, *args, **kwargs) -> str:
        client: "Asteroid" = self.client  # type: ignore
        return client.i18n.get_translate(key, self.locale).format(*args, **kwargs)


class CommandContext(context.CommandContext, CustomContext):
    ...


class ComponentContext(context.ComponentContext, CustomContext):
    ...
