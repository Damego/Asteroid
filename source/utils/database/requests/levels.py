from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest

# * A bit of reflection
"""
What if I made some changes to leveling?

BEFORE:
{
    "_id": "roles_by_level",
    "1": 12345,
    "2": 23456,
    "3": 34567
}

AFTER:
{
    "_id": "leveling",
    "roles_by_level": {
        1: 12345
        2: 23456
        3: 34567
    },
    "is_disabled": False
}

This can expand leveling and I can new stuff to leveling in the future.
"""


class LevelRolesRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(
            type, CollectionType.CONFIGURATION, guild_id, DocumentType.ROLES_BY_LEVEL, data
        )

    async def add(self, guild_id: int, level: int, role_id: int):
        data = {str(level): role_id}
        await self._update(OperatorType.SET, guild_id, data)

    async def remove(self, guild_id: int, level: int):
        data = {str(level): ""}
        await self._update(OperatorType.UNSET, guild_id, data)

    async def reset(self, guild_id: int):
        await self._client[str(guild_id)].delete_one({"_id": DocumentType.ROLES_BY_LEVEL.value})

    async def replace(self, guild_id: int, role_id: int, old_level: int, new_level: int):
        data = {
            OperatorType.UNSET.value: {str(old_level): ""},
            OperatorType.SET.value: {str(new_level): role_id},
        }
        await self._update(guild_id, data)

    async def add_user_to_voice(self, guild_id: int, user_id: int, time: int):
        """This is a part of levels so thats why this method here"""
        data = {str(user_id): time}
        await super()._update(OperatorType.SET, guild_id, DocumentType.VOICE_TIME, data)

    async def remove_user_from_voice(self, guild_id: int, user_id: int):
        """This is a part of levels so thats why this method here"""
        data = {str(user_id): ""}
        await super()._update(OperatorType.UNSET, guild_id, DocumentType.VOICE_TIME, data)
