from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class StarBoardRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(
            type, CollectionType.CONFIGURATION, guild_id, DocumentType.STARBOARD, data
        )

    async def setup(
        self, guild_id: int, *, channel_id: int = None, limit: int = None, is_enabled: bool = True
    ):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        await self._update(OperatorType.SET, guild_id, data)

    async def add_message(self, guild_id: int, message_id: int, starboard_message_id: int):
        data = {f"messages.{message_id}.starboard_message": starboard_message_id}
        await self._update(OperatorType.SET, guild_id, data)

    async def modify(
        self, guild_id: int, *, is_enabled: bool = None, channel_id: int = None, limit: int = None
    ):
        data = {}
        if is_enabled is not None:
            data["is_enabled"] = is_enabled
        if channel_id is not None:
            data["channel_id"] = channel_id
        if limit is not None:
            data["limit"] = limit

        await self._update(guild_id, data)

    async def add_member_to_blacklist(self, guild_id: int, member_id: int):
        await self._update(OperatorType.PUSH, guild_id, {"blacklist.members": member_id})

    async def remove_member_from_blacklist(self, guild_id: int, member_id: int):
        await self._update(OperatorType.PULL, guild_id, {"blacklist.members": member_id})

    async def add_channel_to_blacklist(self, guild_id: int, channel_id: int):
        await self._update(OperatorType.PUSH, guild_id, {"blacklist.channels": channel_id})

    async def remove_channel_from_blacklist(self, guild_id: int, channel_id: int):
        await self._update(OperatorType.PULL, guild_id, {"blacklist.channels": channel_id})

    async def add_role_to_blacklist(self, guild_id: int, role_id: int):
        await self._update(OperatorType.PUSH, guild_id, {"blacklist.roles": role_id})

    async def remove_role_from_blacklist(self, guild_id: int, role_id: int):
        await self._update(OperatorType.PULL, guild_id, {"blacklist.roles": role_id})
