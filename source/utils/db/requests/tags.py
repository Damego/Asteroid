from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class TagsRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, CollectionType.CONFIGURATION, guild_id, DocumentType.TAGS, data)

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
        current_name: str,
        *,
        name: str = None,
        title: str = None,
        description: str = None,
        author_id: int = None,
        is_embed: bool = None,
    ):
        id = {"_id": DocumentType.TAGS.value, "tags.name": current_name}
        data = {
            "autorole.$.name": name,
            "autorole.$.title": title,
            "autorole.$.description": description,
            "autorole.$.author_id": author_id,
            "autorole.$.is_embed": is_embed,
        }

        await super()._advanced_update(
            OperatorType.SET, CollectionType.CONFIGURATION, guild_id, id, data
        )
