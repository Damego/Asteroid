from ..enums import CollectionType, Document, OperatorType
from .base import Request


class AutoRoleRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, CollectionType.CONFIGURATION, guild_id, Document.AUTOROLE, data)

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
            name: {
                "channel_id": channel_id,
                "content": content,
                "message_id": message_id,
                "autorole_type": autorole_type,
                "component": component,
            }
        }
        await self._update(OperatorType.SET, guild_id, data)

    async def remove(self, guild_id: int, name: str):
        data = {name: ""}
        await self._update(OperatorType.UNSET, guild_id, data)

    async def modify(
        self,
        guild_id: int,
        name: str,
        *,
        channel_id: int = None,
        content: str = None,
        message_id: int = None,
        autorole_type: str = None,
        component: dict = None,
    ):
        data = {}
        if channel_id is not None:
            data[f"{name}.channel_id"] = channel_id
        if content is not None:
            data[f"{name}.content"] = content
        if message_id is not None:
            data[f"{name}.message_id"] = message_id
        if autorole_type is not None:
            data[f"{name}.autorole_type"] = autorole_type
        if component is not None:
            data[f"{name}.component"] = component

        await self._update(guild_id, data)
