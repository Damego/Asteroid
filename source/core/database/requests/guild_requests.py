from ..consts import AsyncMongoClient


class GuildRequests:
    def __init__(self, client: AsyncMongoClient):
        self._client = client
        self._database = client["guilds"]

    def __get_collection(self, *keys):
        collection = self._database
        for key in keys:
            collection = collection[str(key)]
        return collection

    async def find_all_documents(self, guild_id: int):
        main_collection = self.__get_collection(guild_id, "configuration")
        users_collection = self.__get_collection(guild_id, "users")
        data = main_collection.find()
        users_data = users_collection.find()
        return [_ async for _ in data], [_ async for _ in users_data]

    async def __insert_document(self, *keys, data: dict):
        collection = self.__get_collection(*keys)
        await collection.insert_one(data)

    async def __update_document(self, *keys, filter: str | dict, data: dict, upsert: bool = True):
        collection = self.__get_collection(*keys)
        _filter = {"_id": filter} if isinstance(filter, str) else filter
        await collection.update_one(_filter, data, upsert)

    async def get_guild(self, guild_id: int) -> dict:
        ...

    async def add_guild(self, guild_id: int) -> dict:
        data = {"_id": "configuration", "language": "en-US", "embed_color": "0x5865F2"}
        await self.__insert_document(guild_id, "configuration", data=data)
        return data

    async def remove_guild(self, guild_id: int):
        for key in ("configuration", "users"):
            await self._database[str(guild_id)][key].drop()

    async def add_user(self, guild_id: int, user_id: int) -> dict:
        data = {
            "_id": str(user_id),
        }
        await self.__insert_document(guild_id, "users", data=data)
        return data

    async def update_user(self, guild_id: int, user_id: int, data: dict):
        await self.__update_document(guild_id, "users", filter=str(user_id), data=data, upsert=True)
