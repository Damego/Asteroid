from ..enums import GlobalCollectionType, GlobalDocumentType, OperatorType
from .base import GlobalBaseRequest


class GlobalRequest(GlobalBaseRequest):
    def __init__(self, _client) -> None:
        super().__init__(_client)

    async def get_global_data_json(self):
        users_data_cursor = self._client["USERS"].find()
        other_data_cursor = self._client["OTHER"].find()
        return {
            "users": [user_data async for user_data in users_data_cursor],
            "other_data": [data async for data in other_data_cursor],
        }

    async def _set_data_users(self, user_id: int, data: dict):
        await super()._update(
            OperatorType.SET, GlobalCollectionType.USERS, str(user_id), data
        )

    async def _set_data_other(self, data: dict):
        return await super()._update(
            OperatorType.SET, GlobalCollectionType.OTHER, GlobalDocumentType.MAIN, data
        )

    async def add_user(self, user_id: int):
        data = {"_id": str(user_id)}
        await super()._insert(GlobalCollectionType.USERS, data)

    async def remove_user(self, user_id: int):
        await super()._delete(GlobalCollectionType.USERS, str(user_id))

    async def set_user_genshin_data(self, user_id: int, hoyolab_uid: int, game_uid: int):
        data = {"genshin": {"hoyolab_uid": hoyolab_uid, "game_uid": game_uid}}
        await self._set_data_users(user_id, data)

    async def set_genshin_cookies(self, cookies: dict):
        return await self._set_data_other({"genshin_cookies": cookies})

    async def set_fmtm_chapter(self, chapter: str):  # TODO: Remove after June, 17.
        await self._set_data_other({"fly_me_to_the_moon_chapter": chapter})
