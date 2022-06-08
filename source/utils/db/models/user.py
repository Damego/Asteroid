from typing import Dict, List, Union

from ..requests import RequestClient
from .misc import DictMixin


class GuildUser:
    def __init__(self, _request: RequestClient, guild_id: int, **kwargs) -> None:
        self._request = _request.user
        self._id: int = int(kwargs["_id"])
        self._guild_id = guild_id

        self.leveling: UserLevelData = UserLevelData(**kwargs.get("leveling"))
        self.genshin: UserGenshinData = UserGenshinData(**kwargs.get("genshin"))
        self.notes: List[Note] = (
            [Note(self._request, **note_data) for note_data in kwargs["notes"]]
            if "notes" in kwargs
            else []
        )
        self.music_playlists: Dict[str, List[str]] = (
            {name: tracks for name, tracks in kwargs["music_playlists"]}
            if "music_playlists" in kwargs
            else {}
        )

    async def set_genshin_uid(self, hoyolab_uid: int, game_uid: int):
        await self._request.set_genshin_uid(self._guild_id, self.id, hoyolab_uid, game_uid)
        self.genshin.hoyolab_uid = hoyolab_uid
        self.genshin.game_uid = game_uid

    async def increase_leveling(
        self, *, level: int = 0, xp: int = 0, xp_amount: int = 0, voice_time: int = 0
    ):
        await self._request.increase_leveling(
            self._guild_id, self.id, level=level, xp=xp, xp_amount=xp_amount, voice_time=voice_time
        )
        self.leveling.level += level
        self.leveling.xp += xp
        self.leveling.xp_amount += xp_amount
        self.leveling.voice_time += voice_time

    async def set_leveling(
        self, *, level: int = 0, xp: int = 0, xp_amount: int = 0, voice_time: int = 0
    ):
        await self._request.set_leveling(
            self._guild_id, self.id, level=level, xp=xp, xp_amount=xp_amount, voice_time=voice_time
        )
        self.leveling.level = level
        self.leveling.xp = xp
        self.leveling.xp_amount = xp_amount
        self.leveling.voice_time = voice_time

    async def reset_leveling(self):
        await self._request.reset_leveling(self._guild_id, self.id)
        self.leveling.level = 1
        self.leveling.xp = 0
        self.leveling.xp_amount = 0
        self.leveling.voice_time = 0

    async def add_note(self, name: str, content: str, created_at: int, jump_url: str):
        for note in self.notes:
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

    async def remove_note(self, note: Union["Note", dict]):
        await self._request.remove_note(self._guild_id, self.id, note._json)
        self.notes.remove(note)

    async def add_track_to_playlist(self, playlist: str, track: str):
        await self._request.add_track_to_playlist(self._guild_id, self.id, playlist, track)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].append(track)

    async def add_many_tracks(self, playlist: str, tracks: list):
        await self._request.add_many_tracks(self._guild_id, self.id, playlist, tracks)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].extend(tracks)

    async def remove_track_from_playlist(self, playlist: str, track: str):
        await self._request.remove_track_from_playlist(self._guild_id, self.id, playlist, track)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].remove(track)

    async def remove_playlist(self, playlist: str):
        await self._request.remove_playlist(self._guild_id, self.id, playlist)
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
    __slots__ = ("_json", "level", "xp", "xp_amount", "voice_time")
    level: int
    xp: int
    xp_amount: int
    voice_time: int

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for slot in self.__slots__:
            if not slot.startswith("_") and slot not in kwargs:
                setattr(self, slot, 1 if slot == "level" else 0)


class UserGenshinData(DictMixin):
    __slots__ = ("_json", "hoyolab_uid", "game_uid")
    hoyolab_uid: int
    game_uid: int

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
