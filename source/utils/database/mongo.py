import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCursor
from pymongo import MongoClient
from pymongo.collection import Collection

from . import GlobalData, GuildData


class Mongo:
    __slots__ = (
        "_connection",
        "_guilds",
        "_global_data",
        "_global_data_connection",
        "_global_users_connection",
        "_cache",
    )

    def __init__(self, token: str) -> None:
        self._connection: AsyncIOMotorClient | MongoClient = AsyncIOMotorClient(
            token, tlsCAFile=certifi.where()
        )
        self._guilds = self._connection["guilds"]
        self._global_data: GlobalData = None
        self._global_data_connection: Collection = self._connection["GLOBAL"]
        self._global_users_connection: Collection = self._global_data_connection["USERS"]
        self._cache = {}

    async def update_user(self, guild_id: int, user_id: int, update_type: str, data: dict):
        collection = self._guilds[str(guild_id)]["users"]
        await collection.update_one({"_id": str(user_id)}, {update_type: data}, upsert=True)

    async def get_raw_user_data(self, guild_id: int, user_id: int, data: dict = None) -> dict:
        collection = self._guilds[str(guild_id)]["users"]
        user_data = await collection.find_one({"_id": str(user_id)}, data)
        return user_data

    async def add_guild(self, guild_id: int):
        collection = self._guilds[str(guild_id)]["configuration"]
        await collection.update_one(
            {"_id": "configuration"},
            {"$set": {"embed_color": "0x5865F2", "language": "en-US"}},
            upsert=True,
        )

        json_data = await self.__get_guild_raw_data(guild_id)
        self._cache[str(guild_id)] = GuildData(self._guilds, json_data, guild_id)

    async def delete_guild(self, guild_id: int):
        await self._guilds[str(guild_id)]["configuration"].drop()
        await self._guilds[str(guild_id)]["users"].drop()
        del self._cache[str(guild_id)]

    async def __get_guild_raw_data(self, guild_id: int):
        main_data_cursor: AsyncIOMotorCursor = self._guilds[str(guild_id)]["configuration"].find()
        main_data = [data async for data in main_data_cursor]
        users_data_cursor: AsyncIOMotorCursor = self._guilds[str(guild_id)]["users"].find()
        users_data = [user_data async for user_data in users_data_cursor]
        return {"main": main_data, "users": users_data}

    async def get_guild_data(self, guild_id: int) -> GuildData:
        if str(guild_id) not in self._cache:
            print(f"GuildData for {guild_id} not found in cache. Fetching in database...")
            json_data = await self.__get_guild_raw_data(guild_id)
            self._cache[str(guild_id)] = GuildData(self._guilds, json_data, guild_id)
        return self._cache[str(guild_id)]

    async def get_global_data(self):
        if self._global_data is not None:
            return self._global_data
        users_data_cursor = self._global_users_connection.find()
        users = [user_data async for user_data in users_data_cursor]
        self._global_data = GlobalData(self._global_data_connection, users)
        return self._global_data
