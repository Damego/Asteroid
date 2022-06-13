from typing import Union

from ..enums import GlobalCollectionType, GlobalDocumentType, OperatorType
from .base import GlobalBaseRequest


class GlobalRequest(GlobalBaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)
        self.user = GlobalUserRequest(_client)

    async def get_global_data_json(self):
        users_data_cursor = self._client["USERS"].find()
        other_data_cursor = self._client["OTHER"].find()
        return {
            "users": [user_data async for user_data in users_data_cursor],
            "other_data": [data async for data in other_data_cursor],
        }

    async def _set_data(self, data: dict):
        await super()._update(
            OperatorType.SET, GlobalCollectionType.OTHER, GlobalDocumentType.MAIN, data
        )

    async def set_genshin_cookies(self, cookies: dict):
        await self._set_data({"genshin_cookies": cookies})

    async def set_fmtm_chapter(self, chapter: str):  # TODO: Remove after June, 17.
        await self._set_data({"fly_me_to_the_moon_chapter": chapter})


class GlobalUserRequest(GlobalBaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def add_user(self, user_id: int):
        data = {"_id": str(user_id)}
        await super()._insert(GlobalCollectionType.USERS, data)

    async def remove_user(self, user_id: int):
        await super()._delete(GlobalCollectionType.USERS, str(user_id))

    async def _set_data(self, operator_type: OperatorType, id: dict | int | str, data: dict):
        await super()._update(operator_type.value, GlobalCollectionType.USERS, id, data)

    async def set_user_genshin_data(self, user_id: int, hoyolab_uid: int, game_uid: int):
        data = {"genshin": {"hoyolab_uid": hoyolab_uid, "game_uid": game_uid}}
        await self._set_data(OperatorType.SET, user_id, data)

    async def add_track_to_playlist(self, user_id: int, playlist: str, track: str):
        data = {f"music_playlists.{playlist}": track}
        await self._set_data(OperatorType.PUSH, user_id, data)

    async def add_note(
        self,
        user_id: int,
        *,
        name: str,
        content: str,
        created_at: int,
        jump_url: str,
    ):
        data = {
            "notes": {
                "name": name,
                "content": content,
                "created_at": created_at,
                "jump_url": jump_url,
            }
        }
        await self._set_data(OperatorType.SET, user_id, data)

    async def modify_note(
        self,
        user_id: int,
        current_name: str,
        *,
        name: str = None,
        content: str = None,
        created_at: int = None,
        jump_url: str = None,
    ):
        id = {"_id": user_id, "notes.name": current_name}
        data = {}
        if name is not None:
            data["notes.$.name"] = name
        if content is not None:
            data["notes.$.content"] = content
        if created_at is not None:
            data["notes.$.created_at"] = created_at
        if jump_url is not None:
            data["notes.$.jump_url"] = jump_url

        await self._set_data(OperatorType.SET, id, data)

    async def remove_note(self, user_id: int, note: dict):
        data = {"notes": note}
        await self._set_data(OperatorType.PULL, user_id, data)

    async def add_many_tracks(self, user_id: int, playlist: str, tracks: list):
        data = {f"music_playlists.{playlist}": {OperatorType.EACH.value: tracks}}
        await self._set_data(OperatorType.PUSH, user_id, data)

    async def remove_track_from_playlist(self, user_id: int, playlist: str, track: str):
        data = {f"music_playlists.{playlist}": track}
        await self._set_data(OperatorType.PULL, user_id, data)

    async def remove_playlist(self, user_id: int, playlist: str):
        data = {f"music_playlists.{playlist}": ""}
        await self._set_data(OperatorType.UNSET, user_id, data)
