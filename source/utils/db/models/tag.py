from ..requests import RequestClient
from .misc import DictMixin


class GuildTag(DictMixin):
    __slots__ = (
        "_json",
        "_request",
        "guild_id",
        "name",
        "author_id",
        "is_embed",
        "title",
        "description",
    )
    name: str
    author_id: int
    is_embed: bool
    title: str
    description: str

    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        self._request = _request.tags
        self._guild_id = guild_id
        super().__init__(kwargs)

    async def modify(self, **kwargs):
        """
        Parameters:
        name: str
        author_id: int
        is_embed: bool
        title: str
        description: str
        """
        await self._request.modify(self._guild_id, self.name, **kwargs)
        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)
