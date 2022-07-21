from ..consts import Language
from .attrs_utils import (
    DataBaseSerializerMixin,
    DictSerializerMixin,
    convert_int,
    convert_list,
    define,
    field,
    int16,
)

__all__ = [
    "GuildUserLeveling",
    "GuildUser",
    "GuildSettings",
    "GuildAutoRole",
    "GuildTag",
    "GuildPrivateVoice",
    "GuildLeveling",
    "GuildEmojiMessage",
    "GuildEmojiBoard",
    "GuildData",
]


@define()
class GuildUserLeveling(DictSerializerMixin):
    level: int = field(converter=convert_int, default=0)  # TODO: Add enum for default value
    xp: int = field(converter=convert_int, default=0)  # TODO: Add enum for default value
    xp_amount: int = field(converter=convert_int, default=0)  # TODO: Add enum for default value


@define()
class GuildUser(DataBaseSerializerMixin):
    id: int = field(converter=int, alias="_id", default=None)
    leveling: GuildUserLeveling = field(converter=GuildUserLeveling, default=None)
    voice_time: int = field(default=0, alias="voice_time_count")
    music_playlists: list[str] = field(factory=list)


@define()
class GuildSettings(DataBaseSerializerMixin):
    language: Language = field(converter=Language)
    embed_color: int = field(converter=int16)
    on_join_roles: list[int] = field(factory=list)
    disabled_commands: list[str] = field(factory=list)
    suggested_russian: bool = field(default=False)


@define()
class GuildAutoRole(DataBaseSerializerMixin):
    name: str = field()
    content: str = field()
    channel_id: int = field()
    message_id: int = field()
    type: str = field(alias="autorole_type")
    component: dict = field()


@define()
class GuildTag(DataBaseSerializerMixin):
    title: str = field()
    description: str = field()
    author_id: int = field()
    is_embed: bool = field()
    created_at: int = field()
    last_edited_at: int = field()
    uses_count: int = field()


@define()
class GuildPrivateVoice(DictSerializerMixin):
    active_channels: list[int] = field(factory=list)
    text_channel_id: int = field()
    voice_channel_id: int = field()


@define()
class GuildLeveling(DictSerializerMixin):
    roles_by_level: dict[int, int] = field(factory=dict)
    message_xp_range: list[int] = field(factory=list)
    voice_factor: int = field(default=10)  # TODO: Add enum for default value
    start_level_role: int = field(default=None)


@define()
class GuildEmojiMessage(DictSerializerMixin):
    message_id: int = field()
    channel_message_id: int = field()


@define()
class GuildEmojiBoard(DataBaseSerializerMixin):
    name: str = field()
    channel_id: int = field()
    emojis: list[str] = field()
    to_add: int = field()
    to_remove: int = field()
    is_freeze: bool = field()
    messages: list[GuildEmojiMessage] = field(
        converter=convert_list(GuildEmojiMessage), factory=list
    )


@define()
class GuildData(DataBaseSerializerMixin):
    settings: GuildSettings = field(
        converter=GuildSettings, add_database=True, alias="configuration", default=None
    )
    users: list[GuildUser] = field(
        converter=convert_list(GuildUser), add_database=True, add_guild_id=True, default=None
    )
    autoroles: list[GuildAutoRole] = field(
        converter=convert_list(GuildAutoRole), add_database=True, add_guild_id=True, default=None
    )
    tags: list[GuildTag] = field(
        converter=convert_list(GuildTag), add_database=True, add_guild_id=True, default=None
    )
    private_voice: GuildPrivateVoice = field(converter=GuildPrivateVoice, default=None)
    voice_time: dict[str, int] = field(default=None)
    leveling: GuildLeveling = field(converter=GuildLeveling, default=None)
    emojiboards: list[GuildEmojiBoard] = field(converter=convert_list(GuildEmojiBoard))

    async def update(self):
        """
        We still need a _database attr but we shouldn't use this method
        because GuildData is not one document.
        It's a lot of documents.
        """
        raise NotImplementedError

    def get_user(self, user_id: int):
        for user in self.users:
            if user.id == user_id:
                return user

    def get_autorole(self, name: str):
        for autorole in self.autoroles:
            if autorole.name == name:
                return autorole

    def get_emoji_board(self, emoji: str):
        for emoji_board in self.emoji_boards:
            if emoji in emoji_board.emojis:
                return emoji_board

    def get_tag(self, name: str):
        for tag in self.tags:
            if tag.name == name:
                return tag

    async def add_user(self, user_id: int, *, data: dict = None) -> GuildUser:
        ...

    async def remove_user(self, user_id: int):
        ...

    async def add_autorole(
        self,
        *,
        name: str,
        content: str,
        channel_id: int,
        message_id: int,
        type: str,
        component: dict,
    ) -> GuildAutoRole:
        ...

    async def remove_autorole(self, name: str):
        ...

    async def add_emoji_board(
        self,
        *,
        name: str,
        channel_id: int,
        emojis: list[str],
        to_add: int,
        to_remove: int,
    ) -> GuildEmojiBoard:
        ...

    async def remove_emoji_board(self, name: str):
        ...

    async def add_tag(
        self, *, title: str, description: str, author_id: int, is_embed: bool = None
    ) -> GuildTag:
        ...

    async def remove_tag(self, name: str):
        ...
