from motor.motor_asyncio import AsyncIOMotorClient

from .consts import AsyncMongoClient, DocumentType, OperatorType
from .models import GuildData
from .requests import Requests

__all__ = ["DataBaseClient"]


class DataBaseClient:
    def __init__(self, url: str):
        self._client: AsyncMongoClient = AsyncIOMotorClient(url)
        self._req = Requests(self._client)
        self._cache = {}

    async def add_guild(self, guild_id: int) -> GuildData:
        settings_data = await self._req.guild.add_guild(guild_id)
        full_data = {"settings": settings_data}
        guild = GuildData(**full_data)
        self._cache[str(guild_id)] = guild
        return guild

    async def get_guild(self, guild_id: int) -> GuildData:
        guild_id = str(guild_id)
        for id, guild in self._cache.items():
            if id == guild_id:
                return guild

        guild_raw_data = await self._req.guild.get_guild_raw_data(guild_id)
        guild_data = GuildData(**guild_raw_data, _database=self, guild_id=guild_id)
        self._cache[guild_id] = guild_data
        return guild_data

    async def remove_guild(self, guild_id: int):
        await self._req.guild.remove_guild(guild_id)

    async def update_guild(
        self, guild_id: int, document: DocumentType | str | dict, operator: OperatorType, data: dict
    ):
        await self._req.guild.update_document(guild_id, document, operator, data)

    async def update_user(self, guild_id: int, user_id: int, data: dict):
        await self._req.guild.update_user(guild_id, user_id, data)
