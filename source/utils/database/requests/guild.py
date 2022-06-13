from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class GuildRequest(BaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def get_guild(self, guild_id: int):
        main_data_cursor = self._client[str(guild_id)][CollectionType.CONFIGURATION.value].find()
        users_data_cursor = self._client[str(guild_id)][CollectionType.USERS.value].find()

        main_data = [data async for data in main_data_cursor]
        users_data = [user_data async for user_data in users_data_cursor]
        return main_data, users_data

    async def create_guild(self, guild_id: int, data: dict):
        await super()._insert(guild_id, CollectionType.CONFIGURATION, data)

    async def remove_guild(self, guild_id: int):
        await self._client[str(guild_id)][CollectionType.CONFIGURATION.value].drop()
        await self._client[str(guild_id)][CollectionType.USERS.value].drop()
