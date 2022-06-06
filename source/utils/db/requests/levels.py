from ..enums import CollectionType, Document, OperatorType
from .base import Request


class LevelRolesRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(
            type, CollectionType.CONFIGURATION, guild_id, Document.ROLES_BY_LEVEL, data
        )

    async def add(self, guild_id: int, level: int, role_id: int):
        data = {str(level): role_id}
        await self._update(OperatorType.SET, guild_id, data)

    async def remove(self, guild_id: int, level: int):
        data = {str(level): ""}
        await self._update(OperatorType.UNSET, guild_id, data)

    async def reset(self, guild_id: int):
        await self._client[str(guild_id)].delete_one({"_id": Document.ROLES_BY_LEVEL.value})

    async def add_user_to_voice(self, guild_id: int, user_id: int, time: int):
        """This is a part of levels so thats why this method here"""
        data = {str(user_id): time}
        await super()._update(OperatorType.SET, guild_id, Document.VOICE_TIME, data)

    async def remove_user_from_voice(self, guild_id: int, user_id: int):
        """This is a part of levels so thats why this method here"""
        data = {str(user_id): ""}
        await super()._update(OperatorType.UNSET, guild_id, Document.VOICE_TIME, data)
