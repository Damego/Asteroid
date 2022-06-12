from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from ..enums import CollectionType, DocumentType, OperatorType
from .base import BaseRequest


class UserRequest(BaseRequest):
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client

    async def _update(self, type: OperatorType, guild_id: int, user_id: int, data: dict):
        return await super()._update(type, CollectionType.USERS, guild_id, str(user_id), data)

    async def get_user(self, guild_id: int, user_id: int):
        return await super()._find(guild_id, CollectionType.USERS, str(user_id))

    async def add_user(self, guild_id: int, user_id: int = None, data: dict = None):
        if user_id is None and data is None:
            raise

        if user_id is None:
            _data = data
        else:
            _data = (
                {
                    "_id": str(user_id),
                }
                | data
                if data is not None
                else {}
            )
        await super()._insert(guild_id, CollectionType.USERS, _data)

    async def delete_user(self, guild_id: int, user_id: int):
        await super()._delete(guild_id, CollectionType.USERS, str(user_id))

    async def increase_leveling(
        self,
        guild_id: int,
        user_id: int,
        *,
        level: int = 0,
        xp: int = 0,
        xp_amount: int = 0,
        voice_time: int = 0,
    ):
        data = {
            "leveling.level": level,
            "leveling.xp": xp,
            "leveling.xp_amount": xp_amount,
            "voice_time_count": voice_time,
        }
        await self._update(OperatorType.INC, guild_id, user_id, data)

    async def set_leveling(
        self,
        guild_id: int,
        user_id: int,
        *,
        level: int = None,
        xp: int = None,
        xp_amount: int = None,
        voice_time: int = None,
        role_id: int = None,
    ):
        data = {}
        if level is not None:
            data["leveling.level"] = level
        if xp is not None:
            data["leveling.xp"] = xp
        if xp_amount is not None:
            data["leveling.xp_amount"] = xp_amount
        if voice_time is not None:
            data["voice_time_count"] = voice_time
        if role_id is not None:
            data["leveling.role"] = role_id

        await self._update(OperatorType.SET, guild_id, user_id, data)

    async def reset_leveling(self, guild_id: int, user_id: int):
        data = {
            "leveling": {"level": 1, "xp": 0, "xp_amount": 0, "role": ""},
            "voice_time_count": 0,
        }
        await self._update(OperatorType.SET, guild_id, user_id, data)

    async def add_note(
        self,
        guild_id: int,
        user_id: int,
        *,
        name: str,
        content: str,
        created_at: int,
        jump_url: str,
    ):
        data = {
            "name": name,
            "content": content,
            "created_at": created_at,
            "jump_url": jump_url,
        }
        await self._update(OperatorType.PUSH, guild_id, user_id, {"notes": data})

    async def modify_note(
        self,
        guild_id: int,
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

        await super()._advanced_update(OperatorType.SET, CollectionType.USERS, guild_id, id, data)

    async def remove_note(self, guild_id: int, user_id: int, note: dict):
        await self._update(OperatorType.PULL, guild_id, user_id, {"notes": note})

    async def add_track_to_playlist(self, guild_id: int, user_id: int, playlist: str, track: str):
        await self._update(
            OperatorType.PUSH, guild_id, user_id, {f"music_playlists.{playlist}": track}
        )

    async def add_many_tracks(self, guild_id: int, user_id: int, playlist: str, tracks: list):
        await self._update(
            OperatorType.PUSH,
            guild_id,
            user_id,
            {f"music_playlists.{playlist}": {OperatorType.EACH.value: tracks}},
        )

    async def remove_track_from_playlist(
        self, guild_id: int, user_id: int, playlist: str, track: str
    ):
        await self._update(
            OperatorType.PULL, guild_id, user_id, {f"music_playlists.{playlist}": track}
        )

    async def remove_playlist(self, guild_id: int, user_id: int, playlist: str):
        await self._update(
            OperatorType.UNSET, guild_id, user_id, {f"music_playlists.{playlist}": ""}
        )
