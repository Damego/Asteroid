from typing import Dict, List, Union

from ..requests.client import RequestClient
from .base import DictMixin


class GuildUser:
    __slots__ = (
        "_request",
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

    def __init__(self, _request: RequestClient, guild_id: int, data) -> None:
        self._request = _request.user
        self._id: int = int(data["_id"])
        self._guild_id = guild_id
        self._level: int = 1
        self._xp: int = 0
        self._xp_amount: int = 0
        self._role: int = None
        self._voice_time_count: int = 0
        self._hoyolab_uid: int = None
        self._genshin_uid: int = None
        self._notes: List[Note] = []
        self._music_playlists: Dict[str, list] = {}

        # TODO: Rewrite this

        if leveling := data.get("leveling"):
            self._level = leveling.get("level", 1)
            self._xp = int(leveling.get("xp", 0))
            self._xp_amount = int(leveling.get("xp_amount", 0))
            self._role = leveling.get("role", None)
        self._voice_time_count = int(data.get("voice_time_count", 0))

        if genshin := data.get("genshin"):
            self._hoyolab_uid = genshin.get("hoyolab_uid")
            self._genshin_uid = genshin.get("uid")

        if notes := data.get("notes", []):
            self._notes = [Note(self._request, **note_data) for note_data in notes]

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

    async def set_genshin_uid(self, hoyolab_uid: int, game_uid: int):
        await self._request.set_genshin_uid(self._guild_id, self.id, hoyolab_uid, game_uid)
        self._hoyolab_uid = hoyolab_uid
        self._genshin_uid = game_uid

    async def increase_leveling(
        self, *, level: int = 0, xp: int = 0, xp_amount: int = 0, voice_time: int = 0
    ):
        await self._request.increase_leveling(
            self._guild_id, self.id, level=level, xp=xp, xp_amount=xp_amount, voice_time=voice_time
        )
        self._level += level
        self._xp += xp
        self._xp_amount += xp_amount
        self._voice_time_count += voice_time

    async def set_leveling(
        self, *, level: int = 0, xp: int = 0, xp_amount: int = 0, voice_time: int = 0
    ):
        await self._request.set_leveling(
            self._guild_id, self.id, level=level, xp=xp, xp_amount=xp_amount, voice_time=voice_time
        )
        self._level = level
        self._xp = xp
        self._xp_amount = xp_amount
        self._voice_time_count = voice_time

    async def reset_leveling(self):
        await self._request.reset_leveling(self._guild_id, self.id)
        self._level = 1
        self._xp = 0
        self._xp_amount = 0
        self._role = None
        self._voice_time_count = 0

    async def add_note(self, name: str, content: str, created_at: int, jump_url: str):
        for note in self._notes:
            if note.name == name:
                raise  # TODO: Make error system

        await self._request.add_note(
            self._guild_id, self.id, name, content=content, created_at=created_at, jump_url=jump_url
        )
        self._notes.append(
            Note(name=name, content=content, created_at=created_at, jump_url=jump_url)
        )

    async def modify_note(self, name: str, note: "Note"):
        """
        Example of usage:
        ```py
        note = user.notes[0]
        old_name = note.name
        note.name = "new_name"
        note.content = "new content"
        await user.modify_note(old_name, note)
        """
        await self._request.modify_note(self._guild_id, self.id, name, **note._json)

    async def remove_note(self, name: str):
        for note in self._notes:
            if note.name == name:
                break
        else:
            raise  # TODO: Make error system
        await self._request.remove_note(self._guild_id, self.id, note._json)
        self._notes.remove(note)

    async def add_track_to_playlist(self, playlist: str, track: str):
        await self._request.add_track_to_playlist(self._guild_id, self.id, playlist, track)
        if playlist not in self._music_playlists:
            self._music_playlists[playlist] = []
        self._music_playlists[playlist].append(track)

    async def add_many_tracks(self, playlist: str, tracks: list):
        await self._request.add_many_tracks(self._guild_id, self.id, playlist, tracks)
        if playlist not in self._music_playlists:
            self._music_playlists[playlist] = []
        self._music_playlists[playlist].extend(tracks)

    async def remove_track_from_playlist(self, playlist: str, track: str):
        await self._request.remove_track_from_playlist(self._guild_id, self.id, playlist, track)
        if playlist not in self._music_playlists:
            self._music_playlists[playlist] = []
        self._music_playlists[playlist].remove(track)

    async def remove_playlist(self, playlist: str):
        await self._request.remove_playlist(self._guild_id, self.id, playlist)
        if playlist in self._music_playlists:
            del self._music_playlists[playlist]


class Note(DictMixin):  # ? Maybe use dataclass?
    __slots__ = ("_json", "name", "content", "created_at", "jump_url")
    name: str
    content: str
    created_at: int
    jump_url: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
