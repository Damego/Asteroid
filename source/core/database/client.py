from interactions import Snowflake
from motor.motor_asyncio import AsyncIOMotorClient

from ..cache import Storage, cache
from ..error import BotException
from .consts import AsyncMongoClient, DocumentType, OperatorType
from .models import (
    GuildAutoRole,
    GuildData,
    GuildEmojiBoard,
    GuildTag,
    GuildUser,
    GuildVoiceLobbies,
)
from .requests import Requests

__all__ = ["DataBaseClient"]


class DataBaseClient:
    def __init__(self, url: str):
        self._client: AsyncMongoClient = AsyncIOMotorClient(url)
        self._req = Requests(self._client)
        self._cache = cache
        self.guilds_storage: Storage = self._cache[GuildData]

    async def add_guild(self, guild_id: int | Snowflake) -> GuildData:
        settings_data = await self._req.guild.add_guild(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id
        )
        full_data = {"settings": settings_data}
        guild = GuildData(**full_data)
        self.guilds_storage[str(guild_id)] = guild
        return guild

    async def get_guild(self, guild_id: int | Snowflake) -> GuildData:
        _guild_id = str(guild_id)
        for _id, guild in self.guilds_storage.items():
            if _id == _guild_id:
                return guild

        guild_raw_data = await self._req.guild.get_guild_raw_data(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id
        )
        guild_data = GuildData(
            **guild_raw_data,
            _database=self,
            guild_id=int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
        )
        self.guilds_storage[_guild_id] = guild_data
        return guild_data

    async def remove_guild(self, guild_id: int | Snowflake):
        await self._req.guild.remove_guild(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id
        )
        del self.guilds_storage[str(guild_id)]

    async def update_guild(
        self,
        guild_id: int | Snowflake,
        document: DocumentType | str | dict,
        operator: OperatorType,
        data: dict,
    ):
        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id, document, operator, data
        )

    async def add_autorole(
        self,
        guild_id: int | Snowflake,
        *,
        name: str,
        content: str,
        channel_id: int,
        message_id: int,
        type: str,
        component: dict,
    ) -> GuildAutoRole:
        data = {
            "name": name,
            "content": content,
            "channel_id": channel_id,
            "message_id": message_id,
            "type": type,
            "component": component,
        }
        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            DocumentType.AUTOROLES,
            OperatorType.PUSH,
            {"autoroles": data},
        )
        autorole = GuildAutoRole(
            **data,
            _database=self,
            guild_id=int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
        )
        self.guilds_storage[str(guild_id)].autoroles.append(autorole)
        return autorole

    async def remove_autorole(
        self, guild_id: int | Snowflake, *, name: str = None, autorole: GuildAutoRole = None
    ):
        if name is not None and autorole is not None:
            if name != autorole.name:
                raise BotException(1)
        if not name and not autorole:
            raise BotException(2)

        if name is not None:
            for autorole in self.guilds_storage[str(guild_id)].autoroles:
                if autorole.name == name:
                    break
            else:
                raise BotException(3)

        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            DocumentType.AUTOROLES,
            OperatorType.PULL,
            autorole._json,
        )
        self.guilds_storage[str(guild_id)].autoroles.remove(autorole)

    async def add_tag(
        self,
        guild_id: int | Snowflake,
        *,
        name: str,
        title: str,
        description: str,
        author_id: int,
        is_embed: bool,
        created_at: int,
        last_edited_at: int,
        uses_count: int,
    ) -> GuildTag:
        data = {
            "name": name,
            "title": title,
            "description": description,
            "author_id": author_id,
            "is_embed": is_embed,
            "created_at": created_at,
            "last_edited_at": last_edited_at,
            "uses_count": uses_count,
        }
        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            DocumentType.TAGS,
            OperatorType.PUSH,
            {"tags": data},
        )
        tag = GuildTag(
            **data,
            _database=self,
            guild_id=int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
        )
        self.guilds_storage[str(guild_id)].tags.append(tag)
        return tag

    async def remove_tag(
        self, guild_id: int | Snowflake, *, name: str = None, tag: GuildTag = None
    ):
        if name is not None and tag is not None:
            if name != tag.name:
                raise BotException(4)
        if not name and not tag:
            raise Exception(5)

        if name is not None:
            for tag in self.guilds_storage[str(guild_id)].tags:
                if tag.name == name:
                    break
            else:
                raise BotException(6)

        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            DocumentType.TAGS,
            OperatorType.PULL,
            tag._json,
        )
        self.guilds_storage[str(guild_id)].tags.remove(tag)

    async def add_emoji_board(
        self,
        guild_id: int | Snowflake,
        *,
        name: str,
        channel_id: int,
        emojis: list[str],
        to_add: int,
        to_remove: int,
        is_freeze: bool,
        embed_color: int,
    ) -> GuildEmojiBoard:
        data = {
            "name": name,
            "channel_id": channel_id,
            "emojis": emojis,
            "to_add": to_add,
            "to_remove": to_remove,
            "is_freeze": is_freeze,
            "embed_color": embed_color,
        }
        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            DocumentType.EMOJI_BOARDS,
            OperatorType.PUSH,
            {"emoji_boards": data},
        )
        board = GuildEmojiBoard(
            **data,
            _database=self,
            guild_id=int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
        )
        self.guilds_storage[str(guild_id)].emoji_boards.append(board)
        return board

    async def remove_emoji_board(
        self, guild_id: int | Snowflake, *, name: str, emoji_board: GuildEmojiBoard
    ):
        if name is not None and emoji_board is not None:
            if name != emoji_board.name:
                raise BotException(7)
        if not name and not emoji_board:
            raise BotException(8)

        if name is not None:
            for emoji_board in self.guilds_storage[str(guild_id)].emoji_boards:
                if emoji_board.name == name:
                    break
            else:
                raise BotException(9)

        await self._req.guild.update_document(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            DocumentType.EMOJI_BOARDS,
            OperatorType.PULL,
            emoji_board._json,
        )
        self.guilds_storage[str(guild_id)].emoji_boards.remove(emoji_board)

    async def add_user(self, guild_id: int | Snowflake, user_id: int) -> GuildUser:
        data = await self._req.guild.add_user(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id, user_id
        )
        user = GuildUser(
            **data,
            _database=self,
            guild_id=int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
        )
        self.guilds_storage[str(guild_id)].users.append(user)
        return user

    async def remove_user(
        self, guild_id: int | Snowflake, *, user_id: int = None, user: GuildUser = None
    ):
        if user_id is not None and user is not None:
            if user_id != user.id:
                raise BotException(10)
        if not user_id and not user:
            raise BotException(11)

        if user_id is not None:
            for user in self.guilds_storage[str(guild_id)].users:
                if user.id == user_id:
                    break
            else:
                raise BotException(12)

        await self._req.guild.remove_user(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id, user_id
        )
        self.guilds_storage[str(guild_id)].users.remove(user)

    async def update_user(self, guild_id: int | Snowflake, user_id: int, data: dict):
        await self._req.guild.update_user(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id, user_id, data
        )

    async def setup_voice_lobbies(
        self,
        guild_id: int | Snowflake,
        category_channel_id: int | Snowflake,
        voice_channel_id: int | Snowflake,
        text_channel_id: int | Snowflake | None = None,
        private_lobbies: bool = False,
    ):
        data = {
            "active_channels": [],
            "category_channel_id": int(category_channel_id),
            "voice_channel_id": int(voice_channel_id),
            "text_channel_id": int(text_channel_id) if text_channel_id is not None else None,
            "private_lobbies": private_lobbies,
        }
        await self.update_guild(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id,
            "voice_lobbies",
            OperatorType.SET,
            data,
        )
        self.guilds_storage[str(guild_id)].voice_lobbies = GuildVoiceLobbies(
            **data, _database=self, guild_id=guild_id
        )
