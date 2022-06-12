from typing import Dict, List

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

    async def set_fmtm_chapter(self, chapter: str):
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
        self._request = _request.global_
        self.id = int(kwargs["_id"])
        self.genshin = UserGenshinData(**kwargs.get("genshin", {}))

    async def set_genshin_uid(self, hoyolab_uid: int, game_uid: int):
        await self._request.set_user_genshin_data(self.id, hoyolab_uid, game_uid)
        self.genshin = UserGenshinData(hoyolab_uid=hoyolab_uid, game_uid=game_uid)


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
