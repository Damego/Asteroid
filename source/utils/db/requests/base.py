from typing import Union

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from ..enums import CollectionType, Document, OperatorType


class Request:
    __slots__ = "_client"

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
            {"_id": id.value if isinstance(id, Document) else id},
            {operator_type.value: data},
            upsert=True,
        )

    async def _advanced_update(
        self,
        operator_type: OperatorType,
        collection_type: CollectionType,
        guild_id: int,
        id: Union[Document, str, dict],
        data: dict,
    ):
        if isinstance(id, Document):
            _id = {"_id": id.value}
        elif isinstance(id, str):
            _id = {"_id": id}
        elif isinstance(id, dict):
            _id = id
        else:
            raise

        await self._client[str(guild_id)][collection_type.value].update_one(
            _id, {operator_type.value: data}, upsert=True
        )
