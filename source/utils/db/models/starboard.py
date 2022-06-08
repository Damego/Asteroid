from typing import Dict, List

from ..requests.client import RequestClient
from .base import DictMixin


class GuildStarboard:
    __slots__ = (
        "_request",
        "_guild_id",
        "_channel_id",
        "_is_enabled",
        "_limit",
        "_messages",
        "_blacklist",
    )

    def __init__(
        self,
        _request: RequestClient,
        guild_id: int,
        *,
        channel_id: int,
        is_enabled: bool,
        limit: int,
        messages: dict,
        blacklist: dict,
    ) -> None:
        self._request = _request.starboard
        self._guild_id = guild_id
        self._channel_id: int = channel_id
        self._is_enabled: bool = is_enabled
        self._limit: int = limit
        self._messages: Dict[str, Dict[str, int]] = messages
        self._blacklist: StarBoardBlackList = StarBoardBlackList(**blacklist)

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def messages(self) -> Dict[str, Dict[str, int]]:
        return self._messages

    @property
    def blacklist(self) -> "StarBoardBlackList":
        return self._blacklist

    async def add_starboard_message(self, message_id: int, starboard_message_id: int):
        await self._request.add_message(self._guild_id, message_id, starboard_message_id)
        self._messages[str(message_id)] = {"starboard_message": starboard_message_id}

    async def modify(self, **kwargs):
        await self._request.modify(self._guild_id, **kwargs)
        for kwarg, value in kwargs.items():
            setattr(self, f"_{kwarg}", value)

    async def add_member_to_blacklist(self, member_id: int):
        await self._request.add_member_to_blacklist(self._guild_id, member_id)
        self._blacklist.members.append(member_id)

    async def remove_member_from_blacklist(self, member_id: int):
        await self._request.remove_member_from_blacklist(self._guild_id, member_id)
        self._blacklist.members.remove(member_id)

    async def add_channel_to_blacklist(self, channel_id: int):
        await self._request.add_channel_to_blacklist(self._guild_id, channel_id)
        self._blacklist.channels.append(channel_id)

    async def remove_channel_from_blacklist(self, channel_id: int):
        await self._request.remove_channel_from_blacklist(self._guild_id, channel_id)
        self._blacklist.channels.remove(channel_id)

    async def add_role_to_blacklist(self, role_id: int):
        await self._request.add_role_to_blacklist(self._guild_id, role_id)
        self._blacklist.roles.append(role_id)

    async def remove_role_from_blacklist(self, role_id: int):
        await self._request.remove_role_from_blacklist(self._guild_id, role_id)
        self._blacklist.roles.remove(role_id)


class StarBoardBlackList(DictMixin):
    __slots__ = ("_json", "members", "channels", "roles")
    members: List[int]
    channels: List[int]
    roles: List[int]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
