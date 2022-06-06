from ..enums import Document, OperatorType
from .base import Request


class StarBoardRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, guild_id, Document.STARBOARD, data)

    async def setup(
        self, guild_id: int, *, channel_id: int = None, limit: int = None, is_enabled: bool = True
    ):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        await self._update(OperatorType.SET, guild_id, data)

    async def add_message(self, guild_id: int, message_id: int, starboard_message_id: int):
        data = {f"messages.{message_id}.starboard_message": starboard_message_id}
        await self._update(OperatorType.SET, guild_id, data)

    async def set_status(self, guild_id: int, is_enabled: bool):
        await self._update(OperatorType.SET, guild_id, {"is_enabled": is_enabled})

    async def set_channel_id(self, guild_id: int, channel_id: int):
        await self._update(OperatorType.SET, guild_id, {"channel_id": channel_id})

    async def set_limit(self, guild_id: int, limit: int):
        await self._update(OperatorType.SET, guild_id, {"limit": limit})

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
