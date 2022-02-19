from os import getenv

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCursor
from pymongo.collection import Collection
from dotenv import load_dotenv

from .models.guild_data import GuildData


load_dotenv()


class Mongo:
    def __init__(self) -> None:
        self._connection = AsyncIOMotorClient(
            getenv("MONGODB_URL"), tlsCAFile=certifi.where()
        )
        self._guilds = self._connection["guilds"]
        self._cache = {}

    @property
    def connection(self):
        return self._connection

    @property
    def guilds(self):
        return self._guilds

    async def update_user(
        self, guild_id: int, user_id: int, update_type: str, data: dict
    ):
        """
        ## Parameters
        - guild_id: int -- ID of server
        - user_id: int -- ID of user
        - update_type: str -- type of update ('$set', '$inc', etc.)
        - data: dict -- data for update
        """

        collection = self._guilds[str(guild_id)]["users"]
        await collection.update_one(
            {"_id": str(user_id)}, {update_type: data}, upsert=True
        )

    async def get_raw_user_data(
        self, guild_id: int, user_id: int, data: dict = None
    ) -> dict:
        collection = self._guilds[str(guild_id)]["users"]
        user_data = await collection.find_one({"_id": str(user_id)}, data)
        return user_data

    async def add_guild(self, guild_id: int):
        collection = self._guilds[str(guild_id)]["configuration"]
        await collection.update_one(
            {"_id": "configuration"},
            {"$set": {"embed_color": "0x5865F2", "language": "English"}},
            upsert=True,
        )

        json_data = await self.get_guild_raw_data(guild_id)
        self._cache[str(guild_id)] = GuildData(self._guilds, json_data, guild_id)

    async def delete_guild(self, guild_id: int):
        await self._guilds[str(guild_id)]["configuration"].drop()
        await self._guilds[str(guild_id)]["users"].drop()
        del self._cache[str(guild_id)]

    async def get_guild_raw_data(self, guild_id: int):
        main_data_cursor: AsyncIOMotorCursor = self._guilds[str(guild_id)][
            "configuration"
        ].find()
        main_data = [data async for data in main_data_cursor]
        users_data_cursor: AsyncIOMotorCursor = self._guilds[str(guild_id)][
            "users"
        ].find()
        users_data = [user_data async for user_data in users_data_cursor]
        return {"main": main_data, "users": users_data}

    async def get_guild_data(self, guild_id: int) -> GuildData:
        if str(guild_id) not in self._cache:
            print(
                f"GuildData for {guild_id} not found in cache. Fetching in database..."
            )
            json_data = await self.get_guild_raw_data(guild_id)
            self._cache[str(guild_id)] = GuildData(self._guilds, json_data, guild_id)
        return self._cache[str(guild_id)]
