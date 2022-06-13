from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.database import Database

from ..enums import (
    CollectionType,
    DocumentType,
    GlobalCollectionType,
    GlobalDocumentType,
    OperatorType,
)


class BaseRequest:
    __slots__ = "_client"

    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client

    async def _find(
        self, guild_id: int, collection_type: CollectionType, id: dict | str
    ) -> dict | None:
        _id = {"_id": id} if isinstance(id, str) else id
        return await self._client[str(guild_id)][collection_type.value].find_one(_id)

    async def _insert(self, guild_id: int, collection_type: CollectionType, data: dict):
        await self._client[str(guild_id)][collection_type.value].insert_one(data)

    async def _delete(self, guild_id: int, collection_type: CollectionType, id: dict | str):
        _id = {"_id": id} if isinstance(id, str) else id
        await self._client[str(guild_id)][collection_type.value].delete_one(_id)

    async def _update(
        self,
        operator_type: OperatorType,
        collection_type: CollectionType,
        guild_id: int,
        id: DocumentType | str,
        data: dict,
    ):
        await self._client[str(guild_id)][collection_type.value].update_one(
            {"_id": id.value if isinstance(id, DocumentType) else id},
            {operator_type.value: data},
            upsert=True,
        )

    async def _advanced_update(
        self,
        operator_type: OperatorType,
        collection_type: CollectionType,
        guild_id: int,
        id: DocumentType | str | dict,
        data: dict,
    ):
        if isinstance(id, GlobalDocumentType):
            _id = {"_id": id.value}
        elif isinstance(id, dict):
            _id = id
        else:
            _id = {"_id": str(id)}

        await self._client[str(guild_id)][collection_type.value].update_one(
            _id, {operator_type.value: data}, upsert=True
        )


class GlobalBaseRequest(BaseRequest):
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        super().__init__(_client)

    async def _find(self, collection_type: GlobalCollectionType, id: dict | str):
        _id = {"_id": id} if isinstance(id, str) else id
        await self._client[collection_type.value].find_one(_id)

    async def _insert(self, collection_type: GlobalCollectionType, data: dict):
        await self._client[collection_type.value].insert_one(data)

    async def _delete(self, collection_type: GlobalCollectionType, id: dict | str):
        _id = {"_id": id} if isinstance(id, str) else id
        await self._client[collection_type.value].delete_one(_id)

    async def _update(
        self,
        operator_type: OperatorType,
        collection_type: GlobalCollectionType,
        id: GlobalDocumentType | str,
        data: dict,
    ):
        await self._client[collection_type.value].update_one(
            {"_id": id.value if isinstance(id, GlobalDocumentType) else str(id)},
            {operator_type.value: data},
            upsert=True,
        )

    async def _advanced_update(
        self,
        operator_type: OperatorType,
        collection_type: GlobalCollectionType,
        id: GlobalDocumentType | str | dict,
        data: dict,
    ):
        if isinstance(id, GlobalDocumentType):
            _id = {"_id": id.value}
        elif isinstance(id, dict):
            _id = id
        else:
            _id = {"_id": str(id)}

        await self._client[collection_type.value].update_one(
            _id, {operator_type.value: data}, upsert=True
        )
