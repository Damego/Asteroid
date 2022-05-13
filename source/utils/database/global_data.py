from typing import Dict, List, Union

from pymongo.collection import Collection

from .enums import OperatorType


class GlobalData:
    """
    Class representing connection to global users collection
    """

    __slots__ = (
        "_users_connection",
        "_other_connection",
        "_users",
        "_genshin_cookies",
        "_fly_me_to_the_moon_chapter",
    )

    def __init__(self, connection, data: Dict[str, Union[str, List[dict]]]) -> None:
        self._users_connection: Collection = connection["USERS"]
        self._other_connection: Collection = connection["OTHER"]
        self._users: List[GlobalUser] = []
        self._genshin_cookies: dict = {}
        self._fly_me_to_the_moon_chapter: str = None

        self.__load_data(data)

    def __load_data(self, data: dict):
        self._users = [GlobalUser(self._users_connection, user_data) for user_data in data["users"]]

        for document in data["other"]:
            if document["_id"] == "main":
                self._genshin_cookies = document["genshin_cookies"]
                self._fly_me_to_the_moon_chapter = document["fly_me_to_the_moon_chapter"]

    @property
    def users(self) -> List["GlobalUser"]:
        return self._users

    @property
    def genshin_cookies(self) -> dict:
        return self._genshin_cookies

    @property
    def fly_me_to_the_moon_chapter(self) -> str:
        return self._fly_me_to_the_moon_chapter

    async def add_user(self, user_id: int):
        data = {"_id": str(user_id)}
        await self._users_connection.insert_one(data)
        user = GlobalUser(self._users_connection, data)
        self._users.append(user)
        return user

    async def get_user(self, user_id: int):
        for user in self._users:
            if user.id == user_id:
                return user

        return await self.add_user(user_id)

    async def remove_user(self, user_id: int):
        await self._users_connection.delete_one({"_id": str(user_id)})
        del self.users[str(user_id)]

    async def _update(self, type: OperatorType, data: dict):
        await self._other_connection.update_one({"_id": "main"}, {type.value: data})

    async def set_genshin_cookies(self, cookies: dict):
        await self._update(OperatorType.SET, {"genshin_cookies": cookies})
        self._genshin_cookies = cookies

    async def set_fmtm_chapter(self, chapter: str):
        await self._update(OperatorType.SET, {"fly_me_to_the_moon_chapter": chapter})
        self._fly_me_to_the_moon_chapter = chapter


class GlobalUser:
    """
    Class representing global user data
    """

    __slots__ = ("_connection", "_id", "_notes", "_music_playlists")

    def __init__(self, connection, data: dict) -> None:
        self._connection: Collection = connection
        self._id = int(data.get("_id"))
        self._notes: List[dict] = data.get("notes", [])
        self._music_playlists: dict = data.get("music_playlists", {})

    @property
    def id(self) -> int:
        return self._id

    @property
    def notes(self) -> List[dict]:
        return self._notes

    @property
    def music_playlists(self) -> dict:
        return self._music_playlists

    async def _update(self, type: OperatorType, data: dict):
        await self._connection.update_one({"_id": str(self._id)}, {type.value: data}, upsert=True)

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

    async def add_note(self, data: dict):
        await self._update(OperatorType.PUSH, {"notes": data})
        self._notes.append(data)

    async def remove_note(self, note_name: str):
        for note in self.notes:
            if note["name"] == note_name:
                await self._update(OperatorType.PULL, {"notes": note})
                self._notes.remove(note)
                break
