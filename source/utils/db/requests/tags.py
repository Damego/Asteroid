from ..enums import Document, OperatorType
from .base import Request


class TagsRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, guild_id, Document.TAGS, data)

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

    async def modify(self):
        ...
