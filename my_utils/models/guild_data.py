from enum import Enum
from typing import Dict, List


class OperatorType(Enum):
    SET = "$set"
    UNSET = "$unset"
    PUSH = "$push"
    PULL = "$pull"
    EACH = "$each"


class GuildData:
    def __init__(self, connection, data: dict, guild_id: int) -> None:
        self._connection = connection[str(guild_id)]
        self._main_collection = self._connection["configuration"]
        self._users_collection = self._connection["users"]
        self.__raw_main_data = data["main"]
        self.__raw_users_data = data["users"]
        self.guild_id = guild_id
        self.configuration = None
        self.starboard = None
        self.autorole = None
        self.roles_by_level = None
        self.reaction_roles = None

        for document in data["main"]:
            if document["_id"] == "configuration":
                self.configuration = GuildConfiguration(self._main_collection, document)
            elif document["_id"] == "starboard":
                self.starboard = GuildStarboard(self._main_collection, document)
            #elif document["_id"] == "autorole":
            #    self.autorole = GuildAutoRole(self._main_collection, document)
            #elif document["_id"] == 'roles_by_level':
            #    self.roles_by_level = document
            #elif document["_id"] == 'reaction_roles':
            #    self.reaction_roles = document

    async def add_starboard(self, *, channel_id: int = None, limit: int = None, is_enabled: bool = True):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        await self._main_collection.update_one(
            {"_id": "starboard"},
            {OperatorType.SET.value: data},
            upsert=True
        )
        self.starboard = GuildStarboard(self._main_collection, data)

class GuildConfiguration:
    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._embed_color: str = data.get("embed_color", "0x5865F2")
        self._on_join_roles: List[int] = data.get("on_join_roles", [])
        self._language: str = data.get("language", "English")
        self._disabled_commands: List[int] = data.get("disabled_commands", [])

    @property
    def embed_color(self):
        return self._embed_color

    @property
    def language(self):
        return self._language
    
    @property
    def on_join_roles(self):
        return self._on_join_roles

    @property
    def disabled_commands(self):
        return self._disabled_commands

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": "configuration"},
            {
                type.value: data
            },
            upsert=True
        )

    async def set_embed_color(self, color):
        await self._update(OperatorType.SET, {"embed_color": color})
        self._embed_color = color

    async def set_language(self, language: str):
        await self._update(OperatorType.SET, {"language": language})
        self._language = language

    async def add_on_join_role(self, role_id: int):
        await self._update(OperatorType.PUSH, {"on_join_roles": role_id})
        self._on_join_roles.append(role_id)

    async def delete_on_join_role(self, role_id: int):
        await self._update(OperatorType.PULL, {"on_join_roles": role_id})
        self._on_join_roles.remove(role_id)

    async def add_disabled_command(self, command_name: str):
        await self._update(OperatorType.PUSH, {"disabled_commands": command_name})
        self._disabled_commands.append(command_name)

    async def delete_disabled_command(self, command_name: str):
        await self._update(OperatorType.PULL, {"disabled_commands": command_name})
        self._disabled_commands.remove(command_name)


class GuildStarboard:
    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self.channel_id: int = data.get("channel_id")
        self.is_enabled: bool = data.get("is_enabled")
        self.limit: int = data.get("limit")
        self.messages: Dict[str, Dict[str, int]] = data.get("messages", {})
        self.blacklist: Dict[str, List[int]] = data.get("blacklist", {"members": [], "channels": [], "roles": []})

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": "starboard"},
            {
                type.value: data
            },
            upsert=True
        )

    async def add_starboard_message(self, message_id: int, starboard_message_id: int):
        await self._update(
            OperatorType.SET,
            {f"messages.{message_id}.starboard_message": starboard_message_id}
        )
        self.messages[str(message_id)] = {
            "starboard_message": starboard_message_id
        }

    async def set_status(self, is_enabled: bool):
        await self._update(
            OperatorType.SET,
            {"is_enabled": is_enabled}
        )
        self.is_enabled = is_enabled

    async def set_channel_id(self, channel_id: int):
        await self._update(
            OperatorType.SET,
            {"channel_id": channel_id}
        )
        self.channel_id = channel_id

    async def set_limit(self, limit: int):
        await self._update(
            OperatorType.SET,
            {"limit": limit}
        )
        self.limit = limit

    async def add_member_to_blacklist(self, member_id: int):
        await self._update(
            OperatorType.PUSH,
            {"blacklist.members": member_id}
        )
        if "members" not in self.blacklist:
            self.blacklist["members"] = []
        self.blacklist["members"].append(member_id)

    async def remove_member_from_blacklist(self, member_id: int):
        await self._update(
            OperatorType.PULL,
            {"blacklist.members": member_id}
        )
        if "members" in self.blacklist and member_id in self.blacklist["members"]:
            self.blacklist["members"].remove(member_id)

    async def add_channel_to_blacklist(self, channel_id: int):
        await self._update(
            OperatorType.PUSH,
            {"blacklist.channels": channel_id}
        )
        if "channels" not in self.blacklist:
            self.blacklist["channels"] = []
        self.blacklist["channels"].append(channel_id)

    async def remove_channel_from_blacklist(self, channel_id: int):
        await self._update(
            OperatorType.PULL,
            {"blacklist.channels": channel_id}
        )
        if "channels" in self.blacklist and channel_id in self.blacklist["channels"]:
            self.blacklist["channels"].remove(channel_id)

    async def add_role_to_blacklist(self, role_id: int):
        await self._update(
            OperatorType.PUSH,
            {"blacklist.roles": role_id}
        )
        if "roles" not in self.blacklist:
            self.blacklist["roles"] = []
        self.blacklist["roles"].append(role_id)

    async def remove_role_from_blacklist(self, role_id: int):
        await self._update(
            OperatorType.PULL,
            {"blacklist.roles": role_id}
        )
        if "roles" in self.blacklist and role_id in self.blacklist["roles"]:
            self.blacklist["roles"].remove(role_id)

class GuildAutoRole:
    ...

class GuildTags:
    ...

class GuildUser:
    ...



