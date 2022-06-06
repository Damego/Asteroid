from ..requests.client import RequestClient


class GuildTag:
    __slots__ = ("_request", "_name", "_author_id", "_is_embed", "_title", "_description")

    def __init__(
        self,
        _request: RequestClient,
        name: str,
        *,
        author_id: int,
        is_embed: bool,
        title: str,
        description: str,
    ) -> None:
        self._request = _request.tags
        self._name: str = name
        self._author_id: int = author_id
        self._is_embed: bool = is_embed
        self._title: str = title
        self._description: str = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def author_id(self) -> int:
        return self._author_id

    @property
    def is_embed(self) -> bool:
        return self._is_embed

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    async def modify(self, name: str, **kwargs):
        await self._request.modify(self._guild_id, name, **kwargs)
        for kwarg, value in kwargs.items():
            setattr(self, f"_{kwarg}", value)
