from time import time
from typing import Dict, List, Union

from ..errors import AlreadyExistException
from ..requests import RequestClient
from .autorole import GuildAutoRole
from .configuration import GuildConfiguration
from .private_voice import GuildPrivateVoice
from .starboard import GuildStarboard
from .tag import GuildTag
from .user import GuildUser


class GuildData:
    __slots__ = (
        "_request",
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
    configuration: GuildConfiguration
    private_voice: GuildPrivateVoice
    starboard: GuildStarboard
    tags: List[GuildTag]
    cogs_data: Dict[str, Dict[str, Union[bool, str]]]
    autoroles: List[GuildAutoRole]
    roles_by_level: Dict[str, int]
    users_voice_time: Dict[str, int]
    users: List[GuildUser]

    def __init__(
        self, _request: RequestClient, guild_id: int, data: List[dict], user_data: List[dict]
    ) -> None:
        self._request = _request
        self.guild_id: int = guild_id

        for document in data:
            if document["_id"] == "configuration":
                self.configuration = GuildConfiguration(self._request, self.guild_id, **document)
            elif document["_id"] == "starboard":
                self.starboard = GuildStarboard(self._request, self.guild_id, **document)
            elif document["_id"] == "tags":
                self.tags = [
                    GuildTag(self._request, self.guild_id, **tag)
                    for tag in document.get("tags", [])
                ]
            elif document["_id"] == "cogs_data":
                self.cogs_data = document
            elif document["_id"] == "autorole":
                self.autoroles = [
                    GuildAutoRole(self._request, self.guild_id, **autorole)
                    for autorole in document.get("autoroles", [])
                ]
            elif document["_id"] == "roles_by_level":
                self.roles_by_level = document
            elif document["_id"] == "voice_time":
                self.users_voice_time = document
            elif document["_id"] == "private_voice":
                self.private_voice = GuildPrivateVoice(self._request, self.guild_id, **document)

        self.users = [GuildUser(self._request, self.guild_id, **user) for user in user_data]
        self.set_default()

    def set_default(self):
        if getattr(self, "configuration", None) is None:
            self.configuration = GuildConfiguration(self._request, self.guild_id)
        if getattr(self, "starboard", None) is None:
            self.starboard = GuildStarboard(self._request, self.guild_id)
        if getattr(self, "tags", None) is None:
            self.tags = []
        if getattr(self, "cogs_data", None) is None:
            self.cogs_data = {}
        if getattr(self, "autoroles", None) is None:
            self.autoroles = []
        if getattr(self, "roles_by_level", None) is None:
            self.roles_by_level = {}
        if getattr(self, "users_voice_time", None) is None:
            self.users_voice_time = {}
        if getattr(self, "private_voice", None) is None:
            self.private_voice = GuildPrivateVoice(self._request, self.guild_id)

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
        if level := self.cogs_data.get("Levels"):
            if not level.get("disabled", False):
                data |= {"leveling": {"role": self.configuration.start_level_role}, "voice_time": 0}
        await self._request.user.add_user(self.guild_id, data=data)
        user = GuildUser(self._request, self.guild_id, **data)
        self.users.append(user)
        return user

    async def get_user(self, user_id: int):
        for user in self.users:
            if user.id == user_id:
                return user
        user = await self.add_user(user_id)
        return user

    async def remove_user(self, user_id: int):
        await self._request.user.delete_user(self.guild_id, user_id)
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
        for autorole in self.autoroles:
            if autorole.name == name:
                raise AlreadyExistException

        data = {
            "name": name,
            "channel_id": channel_id,
            "content": content,
            "message_id": message_id,
            "autorole_type": autorole_type,
            "component": component,
        }

        await self._request.autorole.add(self.guild_id, **data)
        self.autoroles.append(GuildAutoRole(self._request, self.guild_id, **data))

    def get_autorole(self, name: str):
        for autorole in self.autoroles:
            if autorole.name == name:
                return autorole

    async def remove_autorole(self, name: str):
        autorole = self.get_autorole(name)
        await self._request.autorole.remove(self.guild_id, autorole._json)
        self.autoroles.remove(autorole)

    async def add_starboard(
        self, *, channel_id: int = None, limit: int = None, is_enabled: bool = True
    ):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        await self._request.starboard.setup(self.guild_id, **data)
        self.starboard = GuildStarboard(self._request, self.guild_id, **data)

    async def add_tag(
        self,
        *,
        name: str,
        author_id: int,
        title: str,
        description: str,
        is_embed: bool,
        created_at: int,
    ) -> GuildTag:
        for tag in self.tags:
            if tag.name == name:
                raise AlreadyExistException
        data = {
            "name": name,
            "author_id": author_id,
            "title": title,
            "description": description,
            "is_embed": is_embed,
            "created_at": created_at,
            "last_edited_at": None,
            "uses_count": 0,
        }
        await self._request.tags.add(self.guild_id, **data)
        tag = GuildTag(self._request, self.guild_id, **data)
        self.tags.append(tag)
        return tag

    def get_tag(self, name: str) -> GuildTag | None:
        for tag in self.tags:
            if tag.name == name:
                return tag

    async def remove_tag(self, name: str):
        tag = self.get_tag(name)
        await self._request.tags.remove(self.guild_id, tag._json)
        self.tags.remove(tag)

    async def modify_cog(self, cog_name: str, *, is_disabled: bool = None, is_public: bool = None):
        if cog_name not in self.cogs_data:
            self.cogs_data[cog_name] = {}
        if is_disabled is not None:
            self.cogs_data[cog_name]["is_disabled"] = is_disabled
        if is_public is not None:
            self.cogs_data[cog_name]["is_public"] = is_public
        await self._request.configuration.modify_cog(
            self.guild_id, cog_name, is_disabled=is_disabled
        )

    async def add_level_role(self, level: int, role_id: int):
        await self._request.roles_by_level.add(self.guild_id, level, role_id)
        self.roles_by_level[str(level)] = role_id

    async def remove_level_role(self, level: int):
        await self._request.roles_by_level.remove(self.guild_id, level)
        del self.roles_by_level[str(level)]

    async def replace_levels(self, old_level: int, new_level: int):
        role_id = self.roles_by_level[str(old_level)]
        await self._request.roles_by_level.replace(self.guild_id, role_id, old_level, new_level)

        del self.roles_by_level[str(old_level)]
        self.roles_by_level[str(new_level)] = role_id

    async def reset_roles_by_level(self):
        await self._request.roles_by_level.reset(self.guild_id)
        self.roles_by_level = {}
