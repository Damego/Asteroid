import ssl
from typing import Dict, List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCursor
from pymongo import MongoClient

from .models import GlobalData, GuildData
from .requests import RequestClient


class DataBaseClient:
    def __init__(self, mongo_token: str) -> None:
        self.mongo_client: AsyncIOMotorClient | MongoClient = AsyncIOMotorClient(
            mongo_token, ssl_cert_reqs=ssl.CERT_NONE
        )
        self.request_client: RequestClient = RequestClient(self.mongo_client)
        self.guilds: Dict[str, GuildData] = {}
        self.global_data: GlobalData = None

    async def __init(self):
        global_data_json = await self.request_client.global_.get_global_data_json()
        self.global_data = GlobalData(self.request_client, **global_data_json)

    async def get_guild_data(self, guild_id: int):
        if guild_data := self.guilds.get(str(guild_id)):
            return guild_data
        main_data, users_data = await self.request_client.guild.get_guild(guild_id)
        guild_data = GuildData(self.request_client, guild_id, main_data, users_data)
        self.guilds[str(guild_id)] = guild_data
        return guild_data
