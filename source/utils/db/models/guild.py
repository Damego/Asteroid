from time import time
from typing import Dict, List

from ..requests import RequestClient
from .autorole import GuildAutoRole
from .configuration import GuildConfiguration
from .misc import DictMixin
from .private_voice import GuildPrivateVoice
from .starboard import GuildStarboard
from .tag import GuildTag
from .user import GuildUser


class GuildData:
    __slots__ = (
        "_connection",
        "_main_collection",
        "_users_collection",
        "guild_id",
        "configuration",
        "private_voice",
        "starboard",
        "tags",
        "cogs_data",
        "autoroles",
        "roles_by_level",
        "users_voice_time",
        "users",
    )
    guild_id: int
    configuration: GuildConfiguration = None
    private_voice: GuildPrivateVoice = None
    starboard: GuildStarboard = None
    tags: List[GuildTag] = []
    cogs_data: Dict[str, Dict[str, str]] = {}
    autoroles: List[GuildAutoRole] = []
    roles_by_level: Dict[str, str] = {}
    users_voice_time: Dict[str, int] = {}
    users: List[GuildUser] = []

    def __init__(
        self, _request: RequestClient, guild_id: int, data: List[dict], user_data: List[dict]
    ) -> None:
        self._request = _request
        self.guild_id: int = guild_id

        for document in data:
            if document["_id"] == "configuration":
                self.configuration = GuildConfiguration(self._request, document)
            elif document["_id"] == "starboard":
                self.starboard = GuildStarboard(self._request, document)
            elif document["_id"] == "tags":
                self.tags = [
                    GuildTag(self._request, name, data)
                    for name, data in document.items()
                    if name != "_id"
                ]
            elif document["_id"] == "cogs_data":
                self.cogs_data = document
            elif document["_id"] == "autorole":
                self.autoroles = [
                    GuildAutoRole(self._request, name=name, **data)
                    for name, data in document.items()
                    if name != "_id"
                ]
            elif document["_id"] == "roles_by_level":
                self.roles_by_level = document
            elif document["_id"] == "voice_time":
                self.users_voice_time = document
            elif document["_id"] == "private_voice":
                self.private_voice = GuildPrivateVoice(self._request, document)

        self.users = [GuildUser(self._request, user) for user in user_data]

    async def create_private_voice(self, text_channel_id: int, voice_channel_id: int):
        data = await self._request.private_voice.create_private_voice(
            self.guild_id, text_channel_id, voice_channel_id
        )
        self.private_voice = GuildPrivateVoice(self._request, self.guild_id, **data)

    async def add_user_to_voice(self, user_id: int):
        _time = int(time())
        await self._request.roles_by_level.add_user_to_voice(self.guild_id, user_id, _time)
        self.users_voice_time[str(user_id)] = _time

    async def remove_user_from_voice(self, user_id: int):
        await self._request.roles_by_level.remove_user_from_voice(self.guild_id, user_id)
        del self.users_voice_time[str(user_id)]

    async def add_user(self, user_id: int):
        data = {"_id": str(user_id)}
        # TODO: What to do with leveling?
        user = GuildUser(self._users_collection, data)
        self.users.append(user)
        return user

    async def get_user(self, user_id: int):
        for user in self.users:
            if user.id == user_id:
                return user
        print(
            f"UserData for {user_id} not found in `GuildData {self.guild_id}`. Fetching in database..."
        )  # TODO: Use logger
        user_raw_data = await self._users_collection.find_one({"_id": str(user_id)})
        if user_raw_data is None:
            print(f"No data for user {user_id}. Adding user to database...")
            user = await self.add_user(user_id)
        else:
            print(
                f"Founded data for user {user_id} in database. Adding user to `GuildData {self.guild_id}`..."
            )
            user = GuildUser(self._users_collection, user_raw_data)
            self.users.append(user)
        return user

    async def remove_user(self, user_id: int):
        # TODO: Where method?
        for user in self.users:
            if user.id == user_id:
                self.users.remove(user)
                break

    async def add_autorole(
        self,
        *,
        name: str,
        channel_id: int,
        content: str,
        message_id: int,
        autorole_type: str,
        component: dict,
    ):
        data = {
            "channel_id": channel_id,
            "content": content,
            "message_id": message_id,
            "autorole_type": autorole_type,
            "component": component,
        }
        ...
        self.autoroles.append(GuildAutoRole(self._main_collection, name=name, **data))

    def get_autorole(self, name: str):
        for autorole in self.autoroles:
            if autorole.name == name:
                return autorole

    async def remove_autorole(self, name: str):
        ...
        for autorole in self.autoroles:
            if autorole.name == name:
                self.autoroles.remove(autorole)

    async def add_starboard(
        self, *, channel_id: int = None, limit: int = None, is_enabled: bool = True
    ):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        ...
        self.starboard = GuildStarboard(self._main_collection, data)

    async def add_tag(
        self,
        name: str,
        author_id: int,
        description: str,
        is_embed: bool = False,
        title: str = "None",
    ):
        data = {
            "author_id": author_id,
            "description": description,
            "is_embed": is_embed,
            "title": title,
        }
        ...
        self.tags.append(GuildTag(self._main_collection, name, data))

    async def remove_tag(self, name: str):
        ...
        for tag in self.tags:
            if tag.name == name:
                self.tags.remove(tag)

    async def set_cog_data(self, cog_name: str, data: dict):
        self.cogs_data[cog_name] = (
            self.cogs_data[cog_name] | data if self.cogs_data.get(cog_name) else data
        )

        ...

    async def add_level_role(self, level: int, role_id: int):
        ...
        self.roles_by_level[str(level)] = role_id

    async def remove_level_role(self, level: int):
        ...
        del self.roles_by_level[str(level)]

    async def replace_levels(self, old_level: int, new_level: int):
        role = self.roles_by_level[str(old_level)]
        ...
        del self.roles_by_level[str(old_level)]
        self.roles_by_level[str(new_level)] = role

    async def reset_roles_by_level(self):
        ...
        self.roles_by_level = {}


class CogData(DictMixin):
    __slots__ = ("_json", "disabled")
    disabled: bool

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
