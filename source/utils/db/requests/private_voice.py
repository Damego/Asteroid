from ..enums import CollectionType, Document, OperatorType
from .base import Request


class PrivateVoiceRequest(Request):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def _update(type: OperatorType, guild_id: int, data: dict):
        await super()._update(type, CollectionType.CONFIGURATION, guild_id, Document.TAGS, data)

    async def create_private_voice(
        self, guild_id: int, text_channel_id: int, voice_channel_id: int
    ):
        data = {
            "text_channel_id": text_channel_id,
            "voice_channel_id": voice_channel_id,
            "active_channels": {},
        }
        await self._update(OperatorType.SET, guild_id, data)
