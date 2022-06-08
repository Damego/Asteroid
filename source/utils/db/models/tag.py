from ..requests.client import RequestClient
from .base import DictMixin


class GuildTag(DictMixin):
    __slots__ = ("_json", "_request", "name", "author_id", "is_embed", "title", "description")
    name: str
    author_id: int
    is_embed: bool
    title: str
    description: str

    def __init__(self, _request: RequestClient, **kwargs) -> None:
        self._request = _request.tags
        super().__init__(kwargs)

    async def modify(self, **kwargs):
        await self._request.modify(self._guild_id, self.name**kwargs)
        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)
