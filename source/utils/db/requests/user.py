from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from ..enums import CollectionType, Document, OperatorType
from .base import Request


class UserRequest(Request):
    def __init__(self, _client: Database | AsyncIOMotorDatabase) -> None:
        self._client = _client

    async def _update(self, type: OperatorType, guild_id: int, user_id: str, data: dict):
        await super()._update(type, CollectionType.USERS, guild_id, str(user_id), data)

    async def set_genshin_uid(self, guild_id: int, user_id: int, hoyolab_uid: int, game_uid: int):
        data = {"genshin": {"hoyolab_uid": hoyolab_uid, "uid": game_uid}}
        await self._update(OperatorType.SET, guild_id, user_id, data)

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
        name: str,
        *,
        content: str,
        created_at: int,
        jump_url: str,
    ):
        data = {
            "content": content,
            "created_at": created_at,
            "jump_url": jump_url,
        }
        await self._update(OperatorType.SET, guild_id, user_id, {f"notes.{name}": data})

    async def remove_note(self, guild_id: int, user_id: int, name: str):
        await self._update(OperatorType.UNSET, guild_id, user_id, {f"notes.{name}": ""})

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
