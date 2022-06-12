from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from .autorole import AutoRoleRequest
from .configuration import ConfigurationRequest
from .global_ import GlobalRequest
from .guild import GuildRequest
from .levels import LevelRolesRequest
from .private_voice import PrivateVoiceRequest
from .starboard import StarBoardRequest
from .tags import TagsRequest
from .user import UserRequest


class RequestClient:
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client
        self._guilds_client = self._client["guilds"]
        self._global_client = self._client["GLOBAL"]
        self.guild = GuildRequest(self._guilds_client)
        self.autorole = AutoRoleRequest(self._guilds_client)
        self.configuration = ConfigurationRequest(self._guilds_client)
        self.roles_by_level = LevelRolesRequest(self._guilds_client)
        self.private_voice = PrivateVoiceRequest(self._guilds_client)
        self.starboard = StarBoardRequest(self._guilds_client)
        self.tags = TagsRequest(self._guilds_client)
        self.user = UserRequest(self._guilds_client)
        self.global_ = GlobalRequest(self._global_client)
