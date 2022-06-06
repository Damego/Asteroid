from ..enums import Document, OperatorType
from .base import Request


class ConfigurationRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, guild_id, Document.CONFIGURATION, data)

    async def modify_cog(self, guild_id: int, name: str, *, is_disabled: bool):
        ...  # TODO: What to pass here?

    async def set_embed_color(self, guild_id: int, color: int):
        await self._update(OperatorType.SET, guild_id, {"embed_color": color})

    async def set_language(self, guild_id: int, language: str):
        await self._update(OperatorType.SET, guild_id, {"language": language})

    async def add_on_join_role(self, guild_id: int, role_id: int):
        await self._update(OperatorType.PUSH, guild_id, {"on_join_roles": role_id})

    async def remove_on_join_role(self, guild_id: int, role_id: int):
        await self._update(OperatorType.PULL, guild_id, {"on_join_roles": role_id})

    async def add_disabled_command(self, guild_id: int, command_name: str):
        await self._update(OperatorType.PUSH, guild_id, {"disabled_commands": command_name})

    async def remove_disabled_command(self, guild_id: int, command_name: str):
        await self._update(OperatorType.PULL, guild_id, {"disabled_commands": command_name})

    async def set_start_level_role(self, guild_id: int, role_id: int):
        await self._update(OperatorType.SET, guild_id, {"start_level_role": role_id})
