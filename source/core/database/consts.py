from enum import Enum
from typing import TypeAlias

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

__all__ = ["AsyncMongoClient", "Language"]

AsyncMongoClient: TypeAlias = MongoClient | AsyncIOMotorClient


class Language(str, Enum):
    """
    Representing supported languages
    """

    RUSSIAN = "ru"
    ENGlISH = "en-US"
