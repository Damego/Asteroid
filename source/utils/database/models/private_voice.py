from typing import Dict

from ..requests import RequestClient
from .misc import DictMixin


class GuildPrivateVoice(DictMixin):
    __slots__ = (
        "_json",
        "_request",
        "guild_id",
        "text_channel_id",
        "voice_channel_id",
        "active_channels",
    )
    text_channel_id: int
    voice_channel_id: int
    active_channels: Dict[str, int]

    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._request = _request.private_voice
        self.guild_id = guild_id
        self.active_channels = self.active_channels if self.active_channels is not None else {}

    async def set_text_channel(self, channel_id: int):
        await self._request.set_text_channel(self.guild_id, channel_id)
        self.text_channel_id = channel_id

    async def set_voice_channel(self, channel_id: int):
        await self._request.set_voice_channel(self.guild_id, channel_id)
        self.voice_channel_id = channel_id

    async def set_private_voice_channel(
        self,
        member_id: int,
        channel_id: int,
    ):
        await self._request.set_private_voice_channel(self.guild_id, member_id, channel_id)
        self.active_channels[str(member_id)] = channel_id

    async def delete_private_voice_channel(self, member_id: int):
        await self._request.delete_private_voice_channel(self.guild_id, member_id)
        del self.active_channels[str(member_id)]
