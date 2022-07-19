from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

__all__ = ["DataBaseClient"]


class DataBaseClient:
    def __init__(self, url: str):
        self._client: MongoClient | AsyncIOMotorClient = AsyncIOMotorClient(url)
