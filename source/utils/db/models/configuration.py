from typing import List

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
    )
    embed_color: int
    language: str
    on_join_roles: List[int]
    disabled_commands: List[str]
    start_level_role: int

    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        super().__init__(**kwargs)

        self._request = _request.configuration
        self.guild_id = guild_id
        self.embed_color = int(kwargs.get("embed_color", "0x5865F2"), 16)
        self.language = kwargs.get("language", "en-US")
        self.on_join_roles = kwargs.get("on_join_roles", [])
        self.disabled_commands = kwargs.get("disabled_commands", [])
        self.start_level_role = kwargs.get("start_level_role", None)

    async def set_embed_color(self, color: int):
        await self._request.set_embed_color(self.guild_id, color)
        self.embed_color = color

    async def set_language(self, language: str):
        await self._request.set_language(self.guild_id, language)
        self.language = language

    async def set_start_level_role(self, role_id: int):
        await self._request.set_start_level_role(self.guild_id, role_id)
        self.start_level_role = role_id

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
