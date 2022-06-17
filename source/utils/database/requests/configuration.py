from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class ConfigurationRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(self, type: OperatorType, guild_id: int, data: dict):
        await super()._update(
            type, CollectionType.CONFIGURATION, guild_id, DocumentType.CONFIGURATION, data
        )

    async def modify_cog(self, guild_id: int, name: str, *, is_disabled: bool):
        data = {"disabled": is_disabled}
        await super()._update(
            OperatorType.SET,
            CollectionType.CONFIGURATION,
            guild_id,
            DocumentType.COGS_DATA,
            {name: data},
        )

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

    async def set_suggested_russian(self, guild_id: int, status: int):
        await self._update(OperatorType.SET, guild_id, {"suggested_russian": status})
