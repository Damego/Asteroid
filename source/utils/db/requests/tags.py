from ..enums import CollectionType, Document, OperatorType
from .base import Request


class TagsRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, CollectionType.CONFIGURATION, guild_id, Document.TAGS, data)

    async def add(
        self,
        guild_id: int,
        *,
        name: str,
        title: str,
        description: str,
        author_id: int,
        is_embed: bool,
    ):
        data = {
            "name": name,
            "author_id": author_id,
            "title": title,
            "description": description,
            "is_embed": is_embed,
        }
        await self._update(OperatorType.PUSH, guild_id, {"tags": data})

    async def remove(self, guild_id: int, data: dict):
        await self._update(OperatorType.PULL, guild_id, {"tags": data})

    async def modify(
        self,
        guild_id: int,
        *,
        name: str = None,
        title: str = None,
        description: str = None,
        author_id: int = None,
        is_embed: bool = None,
    ):
        ...  # TODO: Make modify
