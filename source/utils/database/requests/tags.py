from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class TagsRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(self, type: OperatorType, guild_id: int, data: dict):
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
        created_at: int,
        last_edited_at: int,
        uses_count: int
    ):
        data = {
            "name": name,
            "author_id": author_id,
            "title": title,
            "description": description,
            "is_embed": is_embed,
            "created_at": created_at,
            "last_edited_at": last_edited_at,
            "uses_count": uses_count,
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
        created_at: int = None,
        last_edited_at: int = None,
        uses_count: int = None
    ):
        id = {"_id": DocumentType.TAGS.value, "tags.name": current_name}
        data = {}

        if name is not None:
            data["tags.$.name"] = name
        if title is not None:
            data["tags.$.title"] = title
        if description is not None:
            data["tags.$.description"] = description
        if author_id is not None:
            data["tags.$.author_id"] = author_id
        if is_embed is not None:
            data["tags.$.is_embed"] = is_embed
        if created_at is not None:
            data["tags.$.created_at"] = created_at
        if last_edited_at is not None:
            data["tags.$.last_edited_at"] = last_edited_at
        if uses_count is not None:
            data["tags.$.uses_count"] = uses_count

        await super()._advanced_update(
            OperatorType.SET, CollectionType.CONFIGURATION, guild_id, id, data
        )
