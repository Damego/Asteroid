from typing import Dict, List, Union

from ..errors import AlreadyExistException
from ..requests import RequestClient
from .misc import DictMixin


class BaseUser(DictMixin):
    __slots__ = (
        "_json",
        "_request",
        "id",
        "notes",
        "music_playlists",
    )
    id: int
    notes: List["Note"]
    music_playlists: Dict[str, List[str]]

    def __init__(self, _request: RequestClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self._request = _request
        self.notes = [Note(**note) for note in kwargs.get("notes", [])]
        self.music_playlists = {
            name: tracks for name, tracks in kwargs.get("music_playlists", {}).items()
        }

    async def add_note(self, name: str, content: str, created_at: int, jump_url: str):
        raise NotImplementedError

    def get_note(self, name: str):
        raise NotImplementedError

    async def modify_note(self, name: str, note: "Note"):
        raise NotImplementedError

    async def remove_note(self, note: "Note"):
        raise NotImplementedError

    async def add_track_to_playlist(self, playlist: str, track: str):
        raise NotImplementedError

    async def add_many_tracks(self, playlist: str, tracks: List[str]):
        raise NotImplementedError

    async def remove_track_from_playlist(self, playlist: str, track: str):
        raise NotImplementedError

    async def remove_playlist(self, playlist: str):
        raise NotImplementedError


class GuildUser(BaseUser):
    __slots__ = (
        "_json",
        "_request",
        "id",
        "guild_id",
        "leveling",
        "voice_time_count",
        "notes",
        "music_playlists",
    )
    id: int
    guild_id: int
    leveling: "UserLevelData"
    voice_time_count: int
    notes: List["Note"]
    music_playlists: Dict[str, List[str]]

    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        super().__init__(_request, **kwargs)
        self._request = _request.user
        self.id = int(kwargs["_id"])
        self.guild_id = guild_id
        self.leveling = UserLevelData(**kwargs.get("leveling", {}))
        if self.voice_time_count is None:
            self.voice_time_count = 0

    async def increase_leveling(
        self, *, level: int = 0, xp: int = 0, xp_amount: int = 0, voice_time: int = 0
    ):
        await self._request.increase_leveling(
            self.guild_id, self.id, level=level, xp=xp, xp_amount=xp_amount, voice_time=voice_time
        )
        self.leveling.level += level
        self.leveling.xp += xp
        self.leveling.xp_amount += xp_amount
        self.voice_time_count += voice_time

    async def set_leveling(
        self,
        *,
        level: int = None,
        xp: int = None,
        xp_amount: int = None,
        voice_time: int = None,
        role_id: int = None
    ):
        await self._request.set_leveling(
            self.guild_id,
            self.id,
            level=level,
            xp=xp,
            xp_amount=xp_amount,
            voice_time=voice_time,
            role_id=role_id,
        )
        if level is not None:
            self.leveling.level = level
        if xp is not None:
            self.leveling.xp = xp
        if xp_amount is not None:
            self.leveling.xp_amount = xp_amount
        if role_id is not None:
            self.leveling.role = role_id
        if voice_time is not None:
            self.voice_time_count = voice_time

    async def reset_leveling(self):
        await self._request.reset_leveling(self.guild_id, self.id)
        self.leveling = UserLevelData(level=1, xp=0, xp_amount=0, role=None)
        self.voice_time_count = 0

    async def add_note(self, name: str, content: str, created_at: int, jump_url: str) -> "Note":
        for note in self.notes:
            if note.name == name:
                raise AlreadyExistException

        await self._request.add_note(
            self.guild_id,
            self.id,
            name=name,
            content=content,
            created_at=created_at,
            jump_url=jump_url,
        )
        note = Note(name=name, content=content, created_at=created_at, jump_url=jump_url)
        self.notes.append(note)
        return note

    def get_note(self, name: str) -> Union["Note", None]:
        for note in self.notes:
            if note.name == name:
                return note

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
        await self._request.modify_note(self.guild_id, self.id, name, **note._json)

    async def remove_note(self, note: "Note"):
        await self._request.remove_note(self.guild_id, self.id, note._json)
        self.notes.remove(note)

    async def add_track_to_playlist(self, playlist: str, track: str):
        await self._request.add_track_to_playlist(self.guild_id, self.id, playlist, track)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].append(track)

    async def add_many_tracks(self, playlist: str, tracks: list):
        await self._request.add_many_tracks(self.guild_id, self.id, playlist, tracks)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].extend(tracks)

    async def remove_track_from_playlist(self, playlist: str, track: str):
        await self._request.remove_track_from_playlist(self.guild_id, self.id, playlist, track)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].remove(track)

    async def remove_playlist(self, playlist: str):
        await self._request.remove_playlist(self.guild_id, self.id, playlist)
        if playlist in self.music_playlists:
            del self.music_playlists[playlist]


class Note(DictMixin):
    __slots__ = ("_json", "name", "content", "created_at", "jump_url")
    name: str
    content: str
    created_at: int
    jump_url: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class UserLevelData(DictMixin):
    __slots__ = ("_json", "level", "xp", "xp_amount", "role")
    level: int
    xp: int
    xp_amount: int
    role: int

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for slot in self.__slots__:
            if not slot.startswith("_") and slot not in kwargs:
                if slot == "level":
                    setattr(self, slot, 1)
                elif slot == "role":
                    setattr(self, slot, None)
                else:
                    setattr(self, slot, 0)
