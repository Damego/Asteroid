from typing import Dict, List

from ..requests import RequestClient
from .misc import DictMixin


class GuildStarboard(DictMixin):
    __slots__ = (
        "_json",
        "_request",
        "guild_id",
        "channel_id",
        "is_enabled",
        "limit",
        "messages",
        "blacklist",
    )
    channel_id: int
    is_enabled: bool
    limit: int
    messages: Dict[str, List[int]]
    blacklist: "StarBoardBlackList"

    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        self._request = _request.starboard
        self.guild_id = guild_id
        super().__init__(**kwargs)
        self.blacklist: StarBoardBlackList = (
            StarBoardBlackList(**kwargs["blacklist"]) if "blacklist" in kwargs else None
        )

    async def add_starboard_message(self, message_id: int, starboard_message_id: int):
        await self._request.add_message(self.guild_id, message_id, starboard_message_id)
        self.messages[str(message_id)] = {"starboard_message": starboard_message_id}

    async def modify(self, **kwargs):
        await self._request.modify(self.guild_id, **kwargs)
        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)

    async def add_member_to_blacklist(self, member_id: int):
        await self._request.add_member_to_blacklist(self.guild_id, member_id)
        self.blacklist.members.append(member_id)

    async def remove_member_from_blacklist(self, member_id: int):
        await self._request.remove_member_from_blacklist(self.guild_id, member_id)
        self.blacklist.members.remove(member_id)

    async def add_channel_to_blacklist(self, channel_id: int):
        await self._request.add_channel_to_blacklist(self.guild_id, channel_id)
        self.blacklist.channels.append(channel_id)

    async def remove_channel_from_blacklist(self, channel_id: int):
        await self._request.remove_channel_from_blacklist(self.guild_id, channel_id)
        self.blacklist.channels.remove(channel_id)

    async def add_role_to_blacklist(self, role_id: int):
        await self._request.add_role_to_blacklist(self.guild_id, role_id)
        self.blacklist.roles.append(role_id)

    async def remove_role_from_blacklist(self, role_id: int):
        await self._request.remove_role_from_blacklist(self.guild_id, role_id)
        self.blacklist.roles.remove(role_id)


class StarBoardBlackList(DictMixin):
    __slots__ = ("_json", "members", "channels", "roles")
    members: List[int]
    channels: List[int]
    roles: List[int]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
