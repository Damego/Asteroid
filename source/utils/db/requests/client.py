from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from .autorole import AutoRoleRequest
from .configuration import ConfigurationRequest
from .levels import LevelRolesRequest
from .private_voice import PrivateVoiceRequest
from .starboard import StarBoardRequest
from .tags import TagsRequest


class RequestClient:
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client
        self.autorole = AutoRoleRequest(_client)
        self.configuration = ConfigurationRequest(_client)
        self.roles_by_level = LevelRolesRequest(_client)
        self.private_voice = PrivateVoiceRequest(_client)
        self.starboard = StarBoardRequest(_client)
        self.tags = TagsRequest(_client)
