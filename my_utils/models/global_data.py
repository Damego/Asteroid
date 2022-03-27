from typing import List

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection  # Only for typehints

from .enums import OperatorType


class GlobalData:
    """
    Class representing connection to global users collection
    """

    def __init__(self, connection, users: List[dict]) -> None:
        self._connection: Collection = connection["USERS"]
        self.users = {
            user_data["_id"]: GlobalUserData(self._connection, user_data)
            for user_data in users
        }

    async def add_user(self, user_id: int):
        data = {"_id": str(user_id)}
        await self._connection.insert_one(data)
        user = GlobalUserData(self._connection, data)
        self.users[str(user_id)] = user
        return user

    async def get_user(self, user_id: int):
        for user, data in self.users.items():
            if user == str(user_id):
                return data

        return await self.add_user(user_id)

    async def remove_user(self, user_id: int):
        await self._connection.delete_one({"_id": str(user_id)})
        del self.users[str(user_id)]


class GlobalUserData:
    """
    Class representing global user data
    """

    def __init__(self, connection, data: dict) -> None:
        self._connection: Collection = connection
        self._id = data.get("_id")
        # TODO: Implement methods for notes
        self._notes = data.get("notes", [])
        self._music_playlists = data.get("music_playlists", {})

    @property
    def id(self):
        return self._id

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
