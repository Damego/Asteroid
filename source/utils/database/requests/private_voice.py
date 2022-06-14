from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class PrivateVoiceRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(self, type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, CollectionType.CONFIGURATION, guild_id, DocumentType.TAGS, data)

    async def create_private_voice(
        self, guild_id: int, text_channel_id: int, voice_channel_id: int
    ) -> dict:
        data = {
            "text_channel_id": text_channel_id,
            "voice_channel_id": voice_channel_id,
            "active_channels": {},
        }
        await self._update(OperatorType.SET, guild_id, data)

        return data

    async def set_text_channel(self, guild_id: int, channel_id: int):
        await self._update(OperatorType.SET, guild_id, {"text_channel_id": channel_id})

    async def set_voice_channel(self, guild_id: int, channel_id: int):
        await self._update(OperatorType.SET, guild_id, {"voice_channel_id": channel_id})

    async def set_private_voice_channel(
        self,
        guild_id: int,
        member_id: int,
        channel_id: int,
    ):
        await self._update(OperatorType.SET, guild_id, {f"active_channels.{member_id}": channel_id})

    async def delete_private_voice_channel(self, guild_id: int, member_id: int):
        await self._update(OperatorType.UNSET, guild_id, {f"active_channels.{member_id}": ""})
