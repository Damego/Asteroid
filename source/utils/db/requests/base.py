from typing import Union

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from ..enums import CollectionType, Document, OperatorType


class Request:
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client

    async def _update(
        self,
        operator_type: OperatorType,
        collection_type: CollectionType,
        guild_id: int,
        id: Union[Document, str],
        data: dict,
    ):
        await self._client[str(guild_id)][collection_type.value].update_one(
            {"_id": id.value}, {operator_type.value: data}, upsert=True
        )
