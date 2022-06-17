from typing import List, Union

from ..requests import RequestClient
from .misc import DictMixin


class GuildConfiguration(DictMixin):
    __slots__ = (
        "_json",
        "_request",
        "guild_id",
        "embed_color",
        "language",
        "on_join_roles",
        "disabled_commands",
        "start_level_role",
        "suggested_russian",
    )
    embed_color: Union[str, int]  # It's should be only int but I forgotten I set str in command
    language: str
    on_join_roles: List[int]
    disabled_commands: List[str]
    start_level_role: int
    suggested_russian: bool

    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        super().__init__(**kwargs)

        self._request = _request.configuration
        self.guild_id = guild_id
        self.embed_color = (
            int(self.embed_color, 16) if self.embed_color is not None else int("0x5865F2", 16)
        )
        self.language = self.language if self.language is not None else "en-US"
        self.on_join_roles = self.on_join_roles if self.on_join_roles is not None else []
        self.disabled_commands = (
            self.disabled_commands if self.disabled_commands is not None else []
        )

    async def set_embed_color(self, color: int):
        await self._request.set_embed_color(self.guild_id, color)
        self.embed_color = color

    async def set_language(self, language: str):
        await self._request.set_language(self.guild_id, language)
        self.language = language

    async def set_start_level_role(self, role_id: int):
        await self._request.set_start_level_role(self.guild_id, role_id)
        self.start_level_role = role_id

    async def set_suggested_russian(self, status: bool):
        await self._request.set_suggested_russian(self.guild_id, status)
        self.suggested_russian = status

    async def add_on_join_role(self, role_id: int):
        await self._request.add_on_join_role(self.guild_id, role_id)
        self.on_join_roles.append(role_id)

    async def remove_on_join_role(self, role_id: int):
        await self._request.remove_on_join_role(self.guild_id, role_id)
        self.on_join_roles.remove(role_id)

    async def add_disabled_command(self, command_name: str):
        await self._request.add_disabled_command(self.guild_id, command_name)
        self.disabled_commands.append(command_name)

    async def remove_disabled_command(self, command_name: str):
        await self._request.remove_disabled_command(self.guild_id, command_name)
        self.disabled_commands.remove(command_name)
