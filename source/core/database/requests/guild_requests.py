from ..consts import AsyncCollection, AsyncDatabase, AsyncMongoClient, DocumentType, OperatorType


class GuildRequests:
    def __init__(self, client):
        self._client: AsyncMongoClient = client
        self._database: AsyncDatabase = client["guilds"]

    def __get_collection(self, *keys: str | int) -> AsyncCollection:
        collection = self._database
        for key in keys:
            collection = collection[str(key)]
        return collection

    async def get_guild_raw_data(self, guild_id: int) -> dict:
        main_collection = self.__get_collection(guild_id, "configuration")
        #users_collection = self.__get_collection(guild_id, "users")
        data = [doc async for doc in main_collection.find()]
        #users_data = [doc async for doc in users_collection.find()]
        full_data = {}
        for document in data:
            id = document["_id"]
            match id:
                case "tags" | "autoroles" | "emoji_boards":
                    full_data[id] = document[id]
                case "voice_time":
                    del document["_id"]
                    full_data[id] = document
                case _:
                    full_data[id] = document
        #full_data["users"] = users_data
        return full_data

    async def __get_document(self, *keys: str, data: dict) -> dict | None:
        collection = self.__get_collection(*keys)
        return await collection.find_one(data)

    async def __insert_document(self, *keys: str, data: dict) -> None:
        collection = self.__get_collection(*keys)
        await collection.insert_one(data)

    async def __update_document(
        self,
        *keys,
        filter: DocumentType | str | dict,
        operator: OperatorType,
        data: dict,
        upsert: bool = True
    ) -> None:
        collection = self.__get_collection(*keys)
        _filter = {"_id": filter} if isinstance(filter, (str, DocumentType)) else filter
        await collection.update_one(_filter, {operator: data}, upsert)

    async def update_document(
        self, guild_id: int, document: DocumentType | str | dict, operator: OperatorType, data: dict
    ) -> None:
        await self.__update_document(
            guild_id, "configuration", filter=document, operator=operator, data=data
        )

    async def add_guild(self, guild_id: int) -> dict:
        data = {"_id": "configuration", "language": "en-US"}
        await self.__insert_document(guild_id, "configuration", data=data)
        return data

    async def remove_guild(self, guild_id: int) -> None:
        for key in ("configuration", "users"):
            await self._database[str(guild_id)][key].drop()

    async def add_user(self, guild_id: int, user_id: int) -> dict:
        data = {"_id": str(user_id)}
        await self.__insert_document(guild_id, "users", data=data)
        return data

    async def get_user(self, guild_id: int, user_id: int) -> dict | None:
        data = {"_id": str(user_id)}
        return await self.__get_document(guild_id, "users", data=data)

    async def remove_user(self, guild_id: int, user_id: int) -> None:
        data = {"_id": str(user_id)}
        collection = self.__get_collection(guild_id, "users")
        await collection.delete_one(data)

    async def update_user(self, guild_id: int, user_id: int, data: dict) -> None:
        await self.__update_document(
            guild_id, "users", filter=str(user_id), operator=OperatorType.SET, data=data
        )
