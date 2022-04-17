from time import time
from typing import Dict, List, Union

from pymongo.collection import Collection

from utils.errors import NotGuild

from .enums import OperatorType


class GuildData:
    __slots__ = (
        "_connection",
        "_main_collection",
        "_users_collection",
        "__raw_main_data",
        "__raw_users_data",
        "guild_id",
        "configuration",
        "private_voice",
        "starboard",
        "tags",
        "cogs_data",
        "autoroles",
        "roles_by_level",
        "users_voice_time",
        "embed_templates",
        "users",
    )

    def __init__(self, connection, data: dict, guild_id: int) -> None:
        if guild_id is None:
            raise NotGuild
        self._connection = connection[str(guild_id)]
        self._main_collection: Collection = self._connection["configuration"]
        self._users_collection: Collection = self._connection["users"]
        self.__raw_main_data = data["main"]
        self.__raw_users_data = data["users"]
        self.guild_id: int = guild_id
        self.configuration: GuildConfiguration = None
        self.private_voice: GuildPrivateVoice = None
        self.starboard: GuildStarboard = None
        self.tags: List[GuildTag] = []
        self.cogs_data: Dict[str, Dict[str, str]] = {}
        self.autoroles: List[GuildAutoRole] = []
        self.roles_by_level: Dict[str, str] = {}
        self.users_voice_time: Dict[str, int] = {}
        self.embed_templates: Dict[str, dict] = {}

        for document in data["main"]:
            if document["_id"] == "configuration":
                self.configuration = GuildConfiguration(self._main_collection, document)
            elif document["_id"] == "starboard":
                self.starboard = GuildStarboard(self._main_collection, document)
            elif document["_id"] == "tags":
                self.tags = [
                    GuildTag(self._main_collection, name, data)
                    for name, data in document.items()
                    if name != "_id"
                ]
            elif document["_id"] == "cogs_data":
                self.cogs_data = document
            elif document["_id"] == "autorole":
                self.autoroles = [
                    GuildAutoRole(self._main_collection, name, data)
                    for name, data in document.items()
                    if name != "_id"
                ]
            elif document["_id"] == "roles_by_level":
                self.roles_by_level = document
            elif document["_id"] == "voice_time":
                self.users_voice_time = document
            elif document["_id"] == "private_voice":
                self.private_voice = GuildPrivateVoice(self._main_collection, document)

        self.users = [GuildUser(self._users_collection, user) for user in data["users"]]

    async def create_private_voice(self, text_channel_id: int, voice_channel_id: int):
        data = {
            "text_channel_id": text_channel_id,
            "voice_channel_id": voice_channel_id,
            "active_channels": {},
        }

        await self._main_collection.update_one(
            {"_id": "private_voice"},
            {OperatorType.SET.value: data},
            upsert=True,
        )
        self.private_voice = GuildPrivateVoice(self._main_collection, data)

    async def add_user_to_voice(self, user_id: int):
        _time = int(time())
        await self._main_collection.update_one(
            {"_id": "voice_time"},
            {OperatorType.SET.value: {str(user_id): _time}},
            upsert=True,
        )
        self.users_voice_time[str(user_id)] = _time

    async def remove_user_to_voice(self, user_id: int):
        await self._main_collection.update_one(
            {"_id": "voice_time"},
            {OperatorType.UNSET.value: {str(user_id): ""}},
            upsert=True,
        )
        del self.users_voice_time[str(user_id)]

    async def add_user(self, user_id: int):
        data = {"_id": str(user_id)}
        if self.configuration.start_level_role is not None:
            data["leveling"] = {"role": self.configuration.start_level_role}
        await self._users_collection.insert_one(data)
        user = GuildUser(self._users_collection, data)
        self.users.append(user)
        return user

    async def get_user(self, user_id: int):
        for user in self.users:
            if user.id == user_id:
                return user
        print(
            f"UserData for {user_id} not found in `GuildData {self.guild_id}`. Fetching in database..."
        )
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
        await self._users_collection.delete_one({"_id": str(user_id)})
        for user in self.users:
            if user.id == str(user_id):
                self.users.remove(user)
                break

    async def add_autorole(self, name: str, data: dict):
        await self._main_collection.update_one(
            {"_id": "autorole"}, {OperatorType.SET.value: {name: data}}, upsert=True
        )
        self.autoroles.append(GuildAutoRole(self._main_collection, name, data))

    async def remove_autorole(self, name: str):
        await self._main_collection.update_one(
            {"_id": "autorole"}, {OperatorType.UNSET.value: {name: ""}}, upsert=True
        )
        for autorole in self.autoroles:
            if autorole.name == name:
                self.autoroles.remove(autorole)

    async def add_starboard(
        self, *, channel_id: int = None, limit: int = None, is_enabled: bool = True
    ):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        await self._main_collection.update_one(
            {"_id": "starboard"}, {OperatorType.SET.value: data}, upsert=True
        )
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
        await self._main_collection.update_one(
            {"_id": "tags"}, {OperatorType.SET.value: {name: data}}, upsert=True
        )
        self.tags.append(GuildTag(self._main_collection, name, data))

    async def remove_tag(self, name: str):
        await self._main_collection.update_one(
            {"_id": "tags"}, {OperatorType.UNSET.value: {name: ""}}, upsert=True
        )
        for tag in self.tags:
            if tag.name == name:
                self.tags.remove(tag)

    async def set_cog_data(self, cog_name: str, data: dict):
        self.cogs_data[cog_name] = (
            self.cogs_data[cog_name] | data if self.cogs_data.get(cog_name) else data
        )

        await self._main_collection.update_one(
            {"_id": "cogs_data"},
            {OperatorType.SET.value: {cog_name: self.cogs_data[cog_name]}},
            upsert=True,
        )

    async def add_level_role(self, level: int, role_id: int):
        await self._main_collection.update_one(
            {"_id": "roles_by_level"},
            {OperatorType.SET.value: {str(level): role_id}},
            upsert=True,
        )
        self.roles_by_level[str(level)] = role_id

    async def remove_level_role(self, level: int):
        await self._main_collection.update_one(
            {"_id": "roles_by_level"},
            {OperatorType.UNSET.value: {str(level): ""}},
            upsert=True,
        )
        del self.roles_by_level[str(level)]

    async def replace_levels(self, old_level: int, new_level: int):
        role = self.roles_by_level[str(old_level)]
        await self._main_collection.update_one(
            {"_id": "roles_by_level"},
            {"$unset": {str(old_level): ""}, "$set": {str(new_level): role}},
            upsert=True,
        )
        del self.roles_by_level[str(old_level)]
        self.roles_by_level[str(new_level)] = role

    async def reset_roles_by_level(self):
        await self._main_collection.delete_one({"_id": "roles_by_level"})
        self.roles_by_level = {}


class GuildConfiguration:
    __slots__ = (
        "_connection",
        "_embed_color",
        "_language",
        "_on_join_roles",
        "_disabled_commands",
        "_start_level_role",
    )

    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._embed_color: int = int(data.get("embed_color", "0x5865F2"), 16)
        self._language: str = data.get("language", "en-US")
        self._on_join_roles: List[int] = data.get("on_join_roles", [])
        self._disabled_commands: List[str] = data.get("disabled_commands", [])
        self._start_level_role: int = data.get("start_level_role", None)

    @property
    def embed_color(self) -> int:
        return self._embed_color

    @property
    def language(self) -> str:
        return self._language

    @property
    def on_join_roles(self) -> List[int]:
        return self._on_join_roles

    @property
    def disabled_commands(self) -> List[str]:
        return self._disabled_commands

    @property
    def start_role(self) -> int:
        return self._start_level_role

    @property
    def start_level_role(self) -> int:
        return self._start_level_role

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": "configuration"}, {type.value: data}, upsert=True)

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

    async def set_start_level_role(self, role_id: int):
        await self._update(OperatorType.SET, {"start_level_role": role_id})
        self._start_level_role = role_id


class GuildStarboard:
    __slots__ = ("_connection", "_channel_id", "_is_enabled", "_limit", "_messages", "_blacklist")

    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._channel_id: int = data.get("channel_id")
        self._is_enabled: bool = data.get("is_enabled")
        self._limit: int = data.get("limit")
        self._messages: Dict[str, Dict[str, int]] = data.get("messages", {})
        self._blacklist: Dict[str, List[int]] = data.get(
            "blacklist", {"members": [], "channels": [], "roles": []}
        )

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def messages(self) -> Dict[str, Dict[str, int]]:
        return self._messages

    @property
    def blacklist(self) -> Dict[str, List[int]]:
        return self._blacklist

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": "starboard"}, {type.value: data}, upsert=True)

    async def add_starboard_message(self, message_id: int, starboard_message_id: int):
        await self._update(
            OperatorType.SET,
            {f"messages.{message_id}.starboard_message": starboard_message_id},
        )
        self._messages[str(message_id)] = {"starboard_message": starboard_message_id}

    async def set_status(self, is_enabled: bool):
        await self._update(OperatorType.SET, {"is_enabled": is_enabled})
        self._is_enabled = is_enabled

    async def set_channel_id(self, channel_id: int):
        await self._update(OperatorType.SET, {"channel_id": channel_id})
        self._channel_id = channel_id

    async def set_limit(self, limit: int):
        await self._update(OperatorType.SET, {"limit": limit})
        self._limit = limit

    async def add_member_to_blacklist(self, member_id: int):
        await self._update(OperatorType.PUSH, {"blacklist.members": member_id})
        if "members" not in self._blacklist:
            self._blacklist["members"] = []
        self._blacklist["members"].append(member_id)

    async def remove_member_from_blacklist(self, member_id: int):
        await self._update(OperatorType.PULL, {"blacklist.members": member_id})
        if "members" in self._blacklist and member_id in self._blacklist["members"]:
            self._blacklist["members"].remove(member_id)

    async def add_channel_to_blacklist(self, channel_id: int):
        await self._update(OperatorType.PUSH, {"blacklist.channels": channel_id})
        if "channels" not in self._blacklist:
            self._blacklist["channels"] = []
        self._blacklist["channels"].append(channel_id)

    async def remove_channel_from_blacklist(self, channel_id: int):
        await self._update(OperatorType.PULL, {"blacklist.channels": channel_id})
        if "channels" in self._blacklist and channel_id in self._blacklist["channels"]:
            self._blacklist["channels"].remove(channel_id)

    async def add_role_to_blacklist(self, role_id: int):
        await self._update(OperatorType.PUSH, {"blacklist.roles": role_id})
        if "roles" not in self._blacklist:
            self._blacklist["roles"] = []
        self._blacklist["roles"].append(role_id)

    async def remove_role_from_blacklist(self, role_id: int):
        await self._update(OperatorType.PULL, {"blacklist.roles": role_id})
        if "roles" in self._blacklist and role_id in self._blacklist["roles"]:
            self._blacklist["roles"].remove(role_id)


class GuildAutoRole:
    __slots__ = ("_connection", "_name", "_content", "_message_id", "_type", "_component")

    def __init__(self, connection, name: str, data: dict) -> None:
        self._connection = connection
        self._name: str = name
        self._content: str = data.get("content")
        self._message_id: int = data.get("message_id")
        self._type: str = data.get("autorole_type")
        self._component: dict = data.get("component")

    @property
    def name(self) -> str:
        return self._name

    @property
    def content(self) -> str:
        return self._content

    @property
    def message_id(self) -> int:
        return self._message_id

    @property
    def type(self) -> str:
        return self._type

    @property
    def component(self) -> dict:
        return self._component

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": "autorole"}, {type.value: data}, upsert=True)

    async def rename(self, name: int):
        await self._update(OperatorType.RENAME, {self._name: name})
        self._name = name

    async def update_component(self, component_data: Union[dict, list]):
        await self._update(OperatorType.SET, {f"{self._name}.component": component_data})
        self._component = component_data


class GuildTag:
    __slots__ = ("_connection", "_name", "_author_id", "_is_embed", "_title", "_description")

    def __init__(self, connection, name: str, data: dict) -> None:
        self._connection = connection
        self._name: str = name
        self._author_id: int = data["author_id"]
        self._is_embed: bool = data["is_embed"]
        self._title: str = data["title"]
        self._description: str = data["description"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def author_id(self) -> int:
        return self._author_id

    @property
    def is_embed(self) -> bool:
        return self._is_embed

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": "tags"}, {type.value: data}, upsert=True)

    async def rename(self, name: int):
        await self._update(OperatorType.RENAME, {self._name: name})
        self._name = name

    async def set_author_id(self, author_id: int):
        await self._update(OperatorType.SET, {f"{self._name}.author_id": author_id})
        self._author_id = author_id

    async def set_embed(self, is_embed: bool):
        await self._update(OperatorType.SET, {f"{self._name}.is_embed": is_embed})
        self._is_embed = is_embed

    async def set_title(self, title: str):
        await self._update(OperatorType.SET, {f"{self._name}.title": title})
        self._title = title

    async def set_description(self, description: str):
        await self._update(OperatorType.SET, {f"{self._name}.description": description})
        self._description = description


class GuildUser:
    __slots__ = (
        "_connection",
        "_id",
        "_level",
        "_xp",
        "_xp_amount",
        "_role",
        "_voice_time_count",
        "_hoyolab_uid",
        "_genshin_uid",
        "_notes",
        "_music_playlists",
    )

    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._id: int = int(data["_id"])
        self._level: int = 1
        self._xp: int = 0
        self._xp_amount: int = 0
        self._role: int = None
        self._voice_time_count: int = 0
        self._hoyolab_uid: int = None
        self._genshin_uid: int = None
        self._notes: List[dict] = []
        self._music_playlists: Dict[str, list] = {}
        if leveling := data.get("leveling"):
            self._level = leveling.get("level", 1)
            self._xp = leveling.get("xp", 0)
            self._xp_amount = leveling.get("xp_amount", 0)
            self._role = leveling.get("role", None)
        self._voice_time_count = data.get("voice_time_count", 0)

        if genshin := data.get("genshin"):
            self._hoyolab_uid = genshin.get("hoyolab_uid")
            self._genshin_uid = genshin.get("uid")

        if notes := data.get("notes", []):
            self._notes = notes

        if playlists := data.get("music_playlists", {}):
            for name, tracks in playlists.items():
                self._music_playlists[name] = tracks

    @property
    def id(self) -> int:
        return self._id

    @property
    def level(self) -> int:
        return self._level

    @property
    def xp(self) -> int:
        return self._xp

    @property
    def xp_amount(self) -> int:
        return self._xp_amount

    @property
    def role(self) -> int:
        return self._role

    @property
    def voice_time_count(self) -> int:
        return self._voice_time_count

    @property
    def hoyolab_uid(self) -> int:
        return self._hoyolab_uid

    @property
    def genshin_uid(self) -> int:
        return self._genshin_uid

    @property
    def notes(self) -> List[dict]:
        return self._notes

    @property
    def music_playlists(self) -> Dict[str, list]:
        return self._music_playlists

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": self._id}, {type.value: data}, upsert=True)

    async def set_genshin_uid(self, hoyolab_uid: int, game_uid: int):
        await self._update(
            OperatorType.SET, {"genshin": {"hoyolab_uid": hoyolab_uid, "uid": game_uid}}
        )
        self._hoyolab_uid = hoyolab_uid
        self._genshin_uid = game_uid

    async def increase_leveling(
        self, *, level: int = 0, xp: int = 0, xp_amount: int = 0, voice_time: int = 0
    ):
        await self._update(
            OperatorType.INC,
            {
                "leveling.level": level,
                "leveling.xp": xp,
                "leveling.xp_amount": xp_amount,
                "voice_time_count": voice_time,
            },
        )
        self._level += level
        self._xp += xp
        self._xp_amount += xp_amount
        self._voice_time_count += voice_time

    async def set_leveling(
        self,
        *,
        level: int = None,
        xp: int = None,
        xp_amount: int = None,
        voice_time: int = None,
        role_id: int = None,
    ):
        data = {}
        if level is not None:
            data["leveling.level"] = level
            self._level = level
        if xp is not None:
            data["leveling.xp"] = xp
            self._xp = xp
        if xp_amount is not None:
            data["leveling.xp_amount"] = xp_amount
            self._xp_amount = xp_amount
        if voice_time is not None:
            data["voice_time_count"] = voice_time
        if role_id is not None:
            data["leveling.role"] = role_id
            self._role = role_id

        await self._update(OperatorType.SET, data)

    async def reset_leveling(self):
        data = {
            "leveling": {"level": 1, "xp": 0, "xp_amount": 0, "role": ""},
            "voice_time_count": 0,
        }
        await self._update(OperatorType.set, data)
        self._level = 1
        self._xp = 0
        self._xp_amount = 0
        self._role = ""
        self._voice_time_count = 0

    async def add_note(self, data: str):
        await self._update(OperatorType.PUSH, {"notes": data})
        self._notes.append(data)

    async def remove_note(self, note_name: str):
        note = None
        for note in self.notes:
            if note["name"] == note_name:
                break
        if note:
            await self._update(OperatorType.PULL, {"notes": note})
            self._notes.remove(note)

    async def add_track_to_playlist(self, playlist: str, track: str):
        await self._update(OperatorType.PUSH, {f"music_playlists.{playlist}": track})
        if playlist not in self._music_playlists:
            self._music_playlists[playlist] = []
        self._music_playlists[playlist].append(track)

    async def add_many_tracks(self, playlist: str, tracks: list):
        await self._update(
            OperatorType.PUSH,
            {f"music_playlists.{playlist}": {OperatorType.EACH.value: tracks}},
        )
        if playlist not in self._music_playlists:
            self._music_playlists[playlist] = []
        self._music_playlists[playlist].extend(tracks)

    async def remove_track_from_playlist(self, playlist: str, track: str):
        await self._update(OperatorType.PULL, {f"music_playlists.{playlist}": track})
        if playlist not in self._music_playlists:
            self._music_playlists[playlist] = []
        self._music_playlists[playlist].remove(track)

    async def remove_playlist(self, playlist: str):
        await self._update(OperatorType.UNSET, {f"music_playlists.{playlist}": ""})
        if playlist in self._music_playlists:
            del self._music_playlists[playlist]


class GuildPrivateVoice:
    __slots__ = ("_connection", "_text_channel_id", "_voice_channel_id", "_active_channels")

    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._text_channel_id: int = data.get("text_channel_id")
        self._voice_channel_id: int = data.get("voice_channel_id")
        self._active_channels: dict = data.get("active_channels", {})

    @property
    def text_channel_id(self) -> int:
        return self._text_channel_id

    @property
    def voice_channel_id(self) -> int:
        return self._voice_channel_id

    @property
    def active_channels(self) -> dict:
        return self._active_channels

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": "private_voice"}, {type.value: data}, upsert=True)

    async def set_text_channel(self, channel_id: int):
        await self._update(OperatorType.SET, {"text_channel_id": channel_id})
        self._text_channel_id = channel_id

    async def set_voice_channel(self, channel_id: int):
        await self._update(OperatorType.SET, {"voice_channel_id": channel_id})
        self._voice_channel_id = channel_id

    async def set_private_voice_channel(
        self,
        member_id: int,
        channel_id: int,
    ):
        await self._update(OperatorType.SET, {f"active_channels.{member_id}": channel_id})
        self._active_channels[str(member_id)] = channel_id

    async def delete_private_voice_channel(self, member_id: int):
        await self._update(OperatorType.UNSET, {f"active_channels.{member_id}": ""})
        del self._active_channels[str(member_id)]
