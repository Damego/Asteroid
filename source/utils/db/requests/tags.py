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
            name: {
                "author_id": author_id,
                "title": title,
                "description": description,
                "is_embed": is_embed,
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
        title: str = None,
        description: str = None,
        author_id: int = None,
        is_embed: bool = None,
    ):
        data = {}
        if title is not None:
            data[f"{name}.title"] = title
        if description is not None:
            data[f"{name}.description"] = description
        if author_id is not None:
            data[f"{name}.author_id"] = author_id
        if is_embed is not None:
            data[f"{name}.is_embed"] = is_embed

        await self._update(guild_id, data)
