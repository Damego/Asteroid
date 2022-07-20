from ..consts import Language
from .attrs_utils import DataBaseSerializerMixin, DictSerializerMixin, convert_list, define, field

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
    level: int = field(converter=int)
    xp: int = field(converter=int)
    xp_amount: int = field(converter=int)


@define()
class GuildUser(DataBaseSerializerMixin):
    id: int = field(converter=int, alias="_id", default=None)
    leveling: GuildUserLeveling = field(converter=GuildUserLeveling, default=None)
    voice_time: int = field(default=None)
    music_playlists: list[str] = field(default=None)


@define()
class GuildSettings(DataBaseSerializerMixin):
    language: Language = field(converter=Language)
    embed_color: int = field(converter=int)
    on_join_roles: list[int] = field(default=None)
    disabled_commands: list[str] = field(default=None)
    start_level_role: int = field(default=None)
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


@define()
class GuildPrivateVoice(DictSerializerMixin):
    active_channels: list[int] = field()
    text_channel_id: int = field()
    voice_channel_id: int = field()


@define()
class GuildLeveling(DictSerializerMixin):
    roles_by_level: dict[int, int] = field(default=None)
    message_factor: list[int] = field(default=None)
    voice_factor: int = field(default=None)


@define()
class GuildEmojiMessage(DictSerializerMixin):
    message_id: int = field()
    channel_message_id: int = field()


@define()
class GuildEmojiBoard(DictSerializerMixin):
    channel_id: int = field()
    emoji: str = field()
    to_add: int = field()
    to_remove: int = field()
    is_freeze: bool = field()
    messages: list[GuildEmojiMessage] = field(converter=convert_list(GuildEmojiMessage))


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
    emoji_boards: list[GuildEmojiBoard] = field(converter=convert_list(GuildEmojiBoard))
