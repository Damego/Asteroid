from typing import Union

from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class AutoRoleRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(
            type, CollectionType.CONFIGURATION, guild_id, DocumentType.AUTOROLE, data
        )

    async def add(
        self,
        guild_id: int,
        *,
        name: str,
        channel_id: int,
        content: str,
        message_id: int,
        autorole_type: str,
        component: dict,
    ):
        data = {
            "name": name,
            "channel_id": channel_id,
            "content": content,
            "message_id": message_id,
            "autorole_type": autorole_type,
            "component": component,
        }
        await self._update(OperatorType.PUSH, guild_id, {"autoroles": data})

    async def remove(self, guild_id: int, data: dict):
        await self._update(OperatorType.PULL, guild_id, {"autoroles": data})

    async def modify(
        self,
        guild_id: int,
        current_name: str,
        *,
        name: str = None,
        channel_id: int = None,
        content: str = None,
        message_id: int = None,
        autorole_type: str = None,
        component: dict = None,
    ):
        id = {"_id": DocumentType.AUTOROLE.value, "autorole.name": current_name}
        data = {}
        if name is not None:
            data["autorole.$.name"] = name
        if channel_id is not None:
            data["autorole.$.channel_id"] = channel_id
        if content is not None:
            data["autorole.$.content"] = content
        if message_id is not None:
            data["autorole.$.message_id"] = message_id
        if autorole_type is not None:
            data["autorole.$.autorole_type"] = autorole_type
        if component is not None:
            data["autorole.$.component"] = component

        await super()._advanced_update(
            OperatorType.SET, CollectionType.CONFIGURATION, guild_id, id, data
        )
