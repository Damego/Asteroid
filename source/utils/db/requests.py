from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from .enums import Document, OperatorType


class GuildDataRequest:
    _client: Database | AsyncIOMotorDatabase

    async def _update(self, type: OperatorType, guild_id: int, id: Document, data: dict):
        await self._client[str(guild_id)].update_one(
            {"_id": id.value}, {type.value: data}, upsert=True
        )

    async def set_embed_color(self, guild_id: int, color: int):
        await self._update(
            OperatorType.SET, guild_id, Document.CONFIGURATION, {"embed_color": color}
        )

    async def set_language(self, guild_id: int, language: str):
        await self._update(
            OperatorType.SET, guild_id, Document.CONFIGURATION, {"language": language}
        )

    async def add_on_join_role(self, guild_id: int, role_id: int):
        await self._update(
            OperatorType.PUSH, guild_id, Document.CONFIGURATION, {"on_join_roles": role_id}
        )

    async def delete_on_join_role(self, guild_id: int, role_id: int):
        await self._update(
            OperatorType.PULL, guild_id, Document.CONFIGURATION, {"on_join_roles": role_id}
        )

    async def add_disabled_command(self, guild_id: int, command_name: str):
        await self._update(
            OperatorType.PUSH, guild_id, Document.CONFIGURATION, {"disabled_commands": command_name}
        )

    async def delete_disabled_command(self, guild_id: int, command_name: str):
        await self._update(
            OperatorType.PULL, guild_id, Document.CONFIGURATION, {"disabled_commands": command_name}
        )

    async def set_start_level_role(self, guild_id: int, role_id: int):
        await self._update(
            OperatorType.SET, guild_id, Document.CONFIGURATION, {"start_level_role": role_id}
        )

    async def create_private_voice(
        self, guild_id: int, text_channel_id: int, voice_channel_id: int
    ):
        data = {
            "text_channel_id": text_channel_id,
            "voice_channel_id": voice_channel_id,
            "active_channels": {},
        }
        await self._update(OperatorType.SET, guild_id, Document.PRIVATE_VOICE, data)

    async def add_user_to_voice(self, guild_id: int, user_id: int, time: int):
        data = {str(user_id): time}
        await self._update(OperatorType.SET, guild_id, Document.VOICE_TIME, data)

    async def remove_user_from_voice(self, guild_id: int, user_id: int):
        data = {str(user_id): ""}
        await self._update(OperatorType.UNSET, guild_id, Document.VOICE_TIME, data)

    async def add_autorole(
        self,
        guild_id: int,
        *,
        name: str,
        channel_id: int,
        content: str,
        message_id: int,
        autorole_type: str,
        component: dict,
    ):
        data = {
            name: {
                "channel_id": channel_id,
                "content": content,
                "message_id": message_id,
                "autorole_type": autorole_type,
                "component": component,
            }
        }
        await self._update(OperatorType.SET, guild_id, Document.AUTOROLE, data)

    async def remove_autorole(self, guild_id: int, name: str):
        data = {name: ""}
        await self._update(OperatorType.UNSET, guild_id, Document.AUTOROLE, data)

    async def starboard_setup(
        self, guild_id: int, *, channel_id: int = None, limit: int = None, is_enabled: bool = True
    ):
        data = {"is_enabled": is_enabled, "channel_id": channel_id, "limit": limit}
        await self._update(OperatorType.SET, guild_id, Document.STARBOARD, data)

    async def starboard_add_message(
        self, guild_id: int, message_id: int, starboard_message_id: int
    ):
        data = {f"messages.{message_id}.starboard_message": starboard_message_id}
        await self._update(OperatorType.SET, guild_id, Document.STARBOARD, data)

    async def starboard_set_status(self, guild_id: int, is_enabled: bool):
        await self._update(
            OperatorType.SET, guild_id, Document.STARBOARD, {"is_enabled": is_enabled}
        )

    async def starboard_set_channel_id(self, guild_id: int, channel_id: int):
        await self._update(
            OperatorType.SET, guild_id, Document.STARBOARD, {"channel_id": channel_id}
        )

    async def starboard_set_limit(self, guild_id: int, limit: int):
        await self._update(OperatorType.SET, guild_id, Document.STARBOARD, {"limit": limit})

    async def starboard_add_member_to_blacklist(self, guild_id: int, member_id: int):
        await self._update(
            OperatorType.PUSH, guild_id, Document.STARBOARD, {"blacklist.members": member_id}
        )

    async def starboard_remove_member_from_blacklist(self, guild_id: int, member_id: int):
        await self._update(
            OperatorType.PULL, guild_id, Document.STARBOARD, {"blacklist.members": member_id}
        )

    async def starboard_add_channel_to_blacklist(self, guild_id: int, channel_id: int):
        await self._update(
            OperatorType.PUSH, guild_id, Document.STARBOARD, {"blacklist.channels": channel_id}
        )

    async def starboard_remove_channel_from_blacklist(self, guild_id: int, channel_id: int):
        await self._update(
            OperatorType.PULL, guild_id, Document.STARBOARD, {"blacklist.channels": channel_id}
        )

    async def starboard_add_role_to_blacklist(self, guild_id: int, role_id: int):
        await self._update(
            OperatorType.PUSH, guild_id, Document.STARBOARD, {"blacklist.roles": role_id}
        )

    async def starboard_remove_role_from_blacklist(self, guild_id: int, role_id: int):
        await self._update(
            OperatorType.PULL, guild_id, Document.STARBOARD, {"blacklist.roles": role_id}
        )

    async def add_tag(
        self,
        guild_id: int,
        *,
        name: str,
        title: str,
        description: str,
        author_id: int,
        is_embed: bool,
    ):
        data = {
            name: {
                "author_id": author_id,
                "title": title,
                "description": description,
                "is_embed": is_embed,
            }
        }
        await self._update(OperatorType.SET, guild_id, Document.TAGS, data)

    async def remove_tag(self, guild_id: int, name: str):
        data = {name: ""}
        await self._update(OperatorType.UNSET, guild_id, Document.TAGS, data)

    async def modify_cog(self, guild_id: int, name: str, *, is_disabled: bool):
        ...  # TODO: What to pass here?

    async def add_level_role(self, guild_id: int, level: int, role_id: int):
        data = {str(level): role_id}
        await self._update(OperatorType.SET, guild_id, Document.ROLES_BY_LEVEL, data)

    async def remove_level_role(self, guild_id: int, level: int):
        data = {str(level): ""}
        await self._update(OperatorType.UNSET, guild_id, Document.ROLES_BY_LEVEL, data)

    async def remove_roles_by_level(self, guild_id: int):
        await self._client[str(guild_id)].delete_one({"_id": Document.ROLES_BY_LEVEL.value})
