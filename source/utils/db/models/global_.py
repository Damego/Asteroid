from typing import Dict, List

from ..requests import RequestClient
from .misc import DictMixin
from .user import BaseUser, Note


class GlobalData:
    __slots__ = ("_request", "users", "other")
    users: List["GlobalUser"]
    other: "MainData"

    def __init__(self, _request: RequestClient, users: List[dict], other_data: List[dict]) -> None:
        self._request = _request
        self.users = [GlobalUser(_request, **user) for user in users]

        for document in other_data:
            if document["_id"] == "main":
                self.other = MainData(**document)


class GlobalUser(BaseUser):
    __slots__ = ("_json", "_request", "id", "notes", "music_playlists", "genshin")
    id: int
    notes: List[Note]
    music_playlists: Dict[str, List[str]]
    genshin: "UserGenshinData"

    def __init__(self, _request: RequestClient, **kwargs) -> None:
        self._request = _request.global_
        super().__init__(**kwargs)

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
