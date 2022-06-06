from ..requests.client import RequestClient


class GuildAutoRole:
    __slots__ = (
        "_request",
        "_guild_id",
        "_name",
        "_channel_id",
        "_content",
        "_message_id",
        "_type",
        "_component",
    )

    def __init__(
        self,
        _request: RequestClient,
        guild_id: int,
        name: str,
        *,
        channel_id: int,
        content: str,
        message_id: int,
        autorole_type: str,
        component: dict,
    ) -> None:
        self._request = _request.autorole
        self._guild_id: int = guild_id
        self._name: str = name
        self._channel_id: int = channel_id
        self._content: str = content
        self._message_id: int = message_id
        self._type: str = autorole_type
        self._component: dict = component

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def content(self) -> str:
        return self._content

    @property
    def message_id(self) -> int:
        return self._message_id

    @property
    def type(self) -> str:
        return self._type

    @property
    def component(self) -> dict:
        return self._component

    async def modify(self, **kwargs):
        """
        Modifies autorole

        Parameters:

        name: str
        channel_id: int
        content: str
        message_id: int
        autorole_type: str
        component: dict
        """
        await self._request.modify(self._guild_id, **kwargs)
        for kwarg, value in kwargs.items():
            setattr(self, f"_{kwarg}", value)
