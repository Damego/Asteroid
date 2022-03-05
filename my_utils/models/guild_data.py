from enum import Enum
from time import time
from typing import Dict, List, Union

from motor.motor_asyncio import AsyncIOMotorCollection


class OperatorType(Enum):
    SET = "$set"
    UNSET = "$unset"
    PUSH = "$push"
    PULL = "$pull"
    EACH = "$each"
    RENAME = "$rename"
    INC = "$inc"


class GuildData:
    def __init__(self, connection, data: dict, guild_id: int) -> None:
        self._connection = connection[str(guild_id)]
        self._main_collection: AsyncIOMotorCollection = self._connection[
            "configuration"
        ]
        self._users_collection: AsyncIOMotorCollection = self._connection["users"]
        self.__raw_main_data = data["main"]
        self.__raw_users_data = data["users"]
        self.guild_id = guild_id
        self.configuration: GuildConfiguration = None
        self.starboard: GuildStarboard = None
        self.tags: List[GuildTag] = []
        self.cogs_data: Dict[str, Dict[str, str]] = {}
        self.autoroles: List[GuildAutoRole] = []
        self.roles_by_level = {}
        self.users_voice_time = {}

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

        self.users = [GuildUser(self._users_collection, user) for user in data["users"]]

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
            if user.id == str(user_id):
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
        self.cogs_data[cog_name] = self.cogs_data[cog_name] | data
        await self._main_collection.update_one(
            {"_id": "cogs_data"},
            {OperatorType.SET.value: {cog_name: self.cogs_data[cog_name]}},
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
    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._embed_color: int = int(data.get("embed_color", "0x5865F2"), 16)
        self._on_join_roles: List[int] = data.get("on_join_roles", [])
        self._language: str = data.get("language", "English")
        self._disabled_commands: List[int] = data.get("disabled_commands", [])
        self._start_level_role: int = data.get("start_level_role", None)

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

    @property
    def start_role(self):
        return self._start_level_role
    
    @property
    def start_level_role(self):
        return self._start_level_role

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": "configuration"}, {type.value: data}, upsert=True
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

    async def set_start_level_role(self, role_id: int):
        await self._update(OperatorType.SET, {"start_level_role": role_id})
        self._start_level_role = role_id


class GuildStarboard:
    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self.channel_id: int = data.get("channel_id")
        self.is_enabled: bool = data.get("is_enabled")
        self.limit: int = data.get("limit")
        self.messages: Dict[str, Dict[str, int]] = data.get("messages", {})
        self.blacklist: Dict[str, List[int]] = data.get(
            "blacklist", {"members": [], "channels": [], "roles": []}
        )

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": "starboard"}, {type.value: data}, upsert=True
        )

    async def add_starboard_message(self, message_id: int, starboard_message_id: int):
        await self._update(
            OperatorType.SET,
            {f"messages.{message_id}.starboard_message": starboard_message_id},
        )
        self.messages[str(message_id)] = {"starboard_message": starboard_message_id}

    async def set_status(self, is_enabled: bool):
        await self._update(OperatorType.SET, {"is_enabled": is_enabled})
        self.is_enabled = is_enabled

    async def set_channel_id(self, channel_id: int):
        await self._update(OperatorType.SET, {"channel_id": channel_id})
        self.channel_id = channel_id

    async def set_limit(self, limit: int):
        await self._update(OperatorType.SET, {"limit": limit})
        self.limit = limit

    async def add_member_to_blacklist(self, member_id: int):
        await self._update(OperatorType.PUSH, {"blacklist.members": member_id})
        if "members" not in self.blacklist:
            self.blacklist["members"] = []
        self.blacklist["members"].append(member_id)

    async def remove_member_from_blacklist(self, member_id: int):
        await self._update(OperatorType.PULL, {"blacklist.members": member_id})
        if "members" in self.blacklist and member_id in self.blacklist["members"]:
            self.blacklist["members"].remove(member_id)

    async def add_channel_to_blacklist(self, channel_id: int):
        await self._update(OperatorType.PUSH, {"blacklist.channels": channel_id})
        if "channels" not in self.blacklist:
            self.blacklist["channels"] = []
        self.blacklist["channels"].append(channel_id)

    async def remove_channel_from_blacklist(self, channel_id: int):
        await self._update(OperatorType.PULL, {"blacklist.channels": channel_id})
        if "channels" in self.blacklist and channel_id in self.blacklist["channels"]:
            self.blacklist["channels"].remove(channel_id)

    async def add_role_to_blacklist(self, role_id: int):
        await self._update(OperatorType.PUSH, {"blacklist.roles": role_id})
        if "roles" not in self.blacklist:
            self.blacklist["roles"] = []
        self.blacklist["roles"].append(role_id)

    async def remove_role_from_blacklist(self, role_id: int):
        await self._update(OperatorType.PULL, {"blacklist.roles": role_id})
        if "roles" in self.blacklist and role_id in self.blacklist["roles"]:
            self.blacklist["roles"].remove(role_id)


class GuildAutoRole:
    def __init__(self, connection, name: str, data: dict) -> None:
        self._connection = connection
        self.name = name
        self.content: str = data.get("content")
        self.message_id: int = data.get("message_id")
        self.type: str = data.get("autorole_type")
        self.component: dict = data.get("component")

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": "autorole"}, {type.value: data}, upsert=True
        )

    async def rename(self, name: int):
        await self._update(OperatorType.RENAME, {self.name: name})
        self.name = name

    async def update_component(self, component_data: Union[dict, list]):
        await self._update(OperatorType.SET, {f"{self.name}.component": component_data})
        self.component = component_data


class GuildTag:
    def __init__(self, connection, name: str, data: dict) -> None:
        self._connection = connection
        self.name: str = name
        self.author_id: int = data["author_id"]
        self.is_embed: bool = data["is_embed"]
        self.title: str = data["title"]
        self.description: str = data["description"]

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": "tags"}, {type.value: data}, upsert=True
        )

    async def rename(self, name: int):
        await self._update(OperatorType.RENAME, {self.name: name})
        self.name = name

    async def set_author_id(self, author_id: int):
        await self._update(OperatorType.SET, {f"{self.name}.author_id": author_id})
        self.author_id = author_id

    async def set_embed(self, is_embed: bool):
        await self._update(OperatorType.SET, {f"{self.name}.is_embed": is_embed})
        self.is_embed = is_embed

    async def set_title(self, title: str):
        await self._update(OperatorType.SET, {f"{self.name}.title": title})
        self.title = title

    async def set_description(self, description: str):
        await self._update(OperatorType.SET, {f"{self.name}.description": description})
        self.description = description


class GuildUser:
    def __init__(self, connection, data: dict) -> None:
        self._connection = connection
        self._id: str = data["_id"]
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
    def id(self):
        return self._id
    
    @property
    def level(self):
        return self._level
    
    @property
    def xp(self):
        return self._xp

    @property
    def xp_amount(self):
        return self._xp_amount

    @property
    def role(self):
        return self._role

    @property
    def voice_time_count(self):
        return self._voice_time_count

    @property
    def hoyolab_uid(self):
        return self._hoyolab_uid

    @property
    def genshin_uid(self):
        return self._genshin_uid

    @property
    def notes(self):
        return self._notes

    @property
    def music_playlists(self):
        return self._music_playlists

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one(
            {"_id": self._id}, {type.value: data}, upsert=True
        )

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

    async def set_genshin_uid(self, *, hoyolab_uid: int = None, game_uid: int = None):
        data = {}
        if hoyolab_uid is not None:
            data["hoyolab_uid"] = hoyolab_uid
            self._hoyolab_uid = hoyolab_uid
        if game_uid is not None:
            data["uid"] = game_uid
            self._genshin_uid = game_uid

        await self._update(OperatorType.SET, {"genshin": data})

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
            {f"music_playlists.{playlist}": {OperatorType.EACH: tracks}},
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
