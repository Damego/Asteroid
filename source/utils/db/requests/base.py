from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from ..enums import Document, OperatorType


class Request:
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client

    async def _update(self, type: OperatorType, guild_id: int, id: Document, data: dict):
        await self._client[str(guild_id)].update_one(
            {"_id": id.value}, {type.value: data}, upsert=True
        )
