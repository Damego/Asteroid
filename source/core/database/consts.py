from enum import Enum
from typing import TypeAlias

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

__all__ = [
    "AsyncMongoClient",
    "AsyncCollection",
    "AsyncDatabase",
    "StrEnum",
    "Language",
    "OperatorType",
    "DocumentType",
]

AsyncMongoClient: TypeAlias = MongoClient | AsyncIOMotorClient
AsyncCollection: TypeAlias = Collection | AsyncIOMotorCollection
AsyncDatabase: TypeAlias = Database | AsyncIOMotorDatabase


class StrEnum(str, Enum):
    ...


class Language(StrEnum):
    """
    Representing supported languages
    """

    RUSSIAN = "ru"
    ENGlISH = "en-US"


class OperatorType(StrEnum):
    SET = "$set"
    UNSET = "$unset"
    PUSH = "$push"
    PULL = "$pull"


class DocumentType(StrEnum):
    SETTINGS = "configuration"
    CONFIGURATION = "configuration"
    AUTOROLES = "autoroles"
    TAGS = "tags"
    EMOJI_BOARDS = "emoji_boards"
    VOICE_LOBBIES = "voice_lobbies"
    LEVELING = "leveling"
