from typing import Dict, List, Union

from ..errors import AlreadyExistException
from ..requests import RequestClient
from .misc import DictMixin
from .user import BaseUser, Note


class GlobalData:
    __slots__ = ("_request", "users", "main")
    users: List["GlobalUser"]
    main: "MainData"

    def __init__(self, _request: RequestClient, users: List[dict], other_data: List[dict]) -> None:
        self._request = _request
        self.users = [GlobalUser(_request, **user) for user in users]

        for document in other_data:
            if document["_id"] == "main":
                self.main = MainData(**document)

    async def set_fmtm_chapter(self, chapter: str):  # TODO: Remove after June, 17
        await self._request.global_.set_fmtm_chapter(chapter)
        self.main.fly_me_to_the_moon_chapter = chapter

    async def add_user(self, user_id: int) -> "GlobalUser":
        await self._request.global_.add_user(user_id)
        user = GlobalUser(self._request, **{"_id": user_id})
        self.users.append(user)
        return user

    async def get_user(self, user_id: int) -> "GlobalUser":
        for user in self.users:
            if user.id == user_id:
                return user
        return await self.add_user(user_id)


class GlobalUser(BaseUser):
    __slots__ = ("_json", "_request", "id", "notes", "music_playlists", "genshin")
    id: int
    notes: List[Note]
    music_playlists: Dict[str, List[str]]
    genshin: "UserGenshinData"

    def __init__(self, _request: RequestClient, **kwargs) -> None:
        super().__init__(_request, **kwargs)
        self._request = _request.global_.user
        self.id = int(kwargs["_id"])
        self.genshin = UserGenshinData(**kwargs.get("genshin", {}))

    async def set_genshin_uid(self, hoyolab_uid: int, game_uid: int):
        await self._request.set_user_genshin_data(self.id, hoyolab_uid, game_uid)
        self.genshin = UserGenshinData(hoyolab_uid=hoyolab_uid, game_uid=game_uid)

    async def add_note(self, name: str, content: str, created_at: int, jump_url: str):
        for note in self.notes:
            if note.name == name:
                raise AlreadyExistException

        await self._request.add_note(
            self.id, name=name, content=content, created_at=created_at, jump_url=jump_url
        )
        self.notes.append(
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
        await self._request.modify_note(self.id, name, **note._json)

    async def remove_note(self, note: Union[Note, dict]):
        note_data = note._json if isinstance(note, Note) else note
        await self._request.remove_note(self.id, note_data)
        self.notes.remove(note)

    async def add_track_to_playlist(self, playlist: str, track: str):
        await self._request.add_track_to_playlist(self.id, playlist, track)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].append(track)

    async def add_many_tracks(self, playlist: str, tracks: list):
        await self._request.add_many_tracks(self.id, playlist, tracks)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].extend(tracks)

    async def remove_track_from_playlist(self, playlist: str, track: str):
        await self._request.remove_track_from_playlist(self.id, playlist, track)
        if playlist not in self.music_playlists:
            self.music_playlists[playlist] = []
        self.music_playlists[playlist].remove(track)

    async def remove_playlist(self, playlist: str):
        await self._request.remove_playlist(self.id, playlist)
        if playlist in self.music_playlists:
            del self.music_playlists[playlist]


class UserGenshinData(DictMixin):
    __slots__ = ("_json", "hoyolab_uid", "game_uid")
    hoyolab_uid: int
    game_uid: int

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class MainData(DictMixin):
    __slots__ = ("_json", "genshin_cookies", "fly_me_to_the_moon_chapter")
    genshin_cookies: Dict[str, str | int]
    fly_me_to_the_moon_chapter: str  # TODO: Remove after June, 17.

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
