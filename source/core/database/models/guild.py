import datetime

from ..consts import Language, OperatorType
from .attrs_utils import (
    DataBaseSerializerMixin,
    DictSerializerMixin,
    ListMixin,
    convert_int,
    convert_list,
    define,
    field,
)

__all__ = [
    "GuildUserLeveling",
    "GuildUser",
    "GuildSettings",
    "GuildAutoRole",
    "GuildTag",
    "GuildVoiceLobbies",
    "GuildLeveling",
    "GuildMessageData",
    "GuildData",
]


@define()
class GuildUserLeveling(DictSerializerMixin):
    level: int = field(converter=convert_int, default=0)  # TODO: Add enum for default value
    xp: int = field(converter=convert_int, default=0)  # TODO: Add enum for default value
    xp_amount: int = field(converter=convert_int, default=0)  # TODO: Add enum for default value
    role: int = field(default=None)


@define()
class GuildUserWarn(DictSerializerMixin):
    author_id: int = field()
    reason: str | None = field(default=None)
    warned_at: datetime.datetime = field()


@define()
class GuildUser(DataBaseSerializerMixin):
    id: int = field(converter=int, alias="_id", default=None)
    leveling: GuildUserLeveling = field(converter=GuildUserLeveling, default=None)
    voice_time: int = field(default=0, alias="voice_time_count")
    music_playlists: list[str] = field(factory=list)
    warns: list[GuildUserWarn] = field(converter=convert_list(GuildUserWarn))

    def add_warn(
        self, author_id: int, warned_at: datetime.datetime, reason: str | None = None
    ) -> GuildUserWarn:
        warn = GuildUserWarn(author_id=author_id, reason=reason, warned_at=warned_at)
        self.warns.append(warn)
        return warn

    def remove_warn(self, index: int) -> None:
        self.warns.pop(index)

    async def update(self):
        await self._database.update_user(self.guild_id, self.id, self.get_changes())


@define()
class GuildSettings(DataBaseSerializerMixin):
    language: Language = field(converter=Language, default=Language.ENGlISH)
    on_join_roles: list[int] = field(factory=list)
    disabled_commands: list[str] = field(factory=list)
    suggested_russian: bool = field(default=False)
    warns_limit: int = field(default=None)

    async def update(self):
        await self._database.update_guild(
            self.guild_id, "configuration", OperatorType.SET, self.get_changes()
        )


@define()
class GuildAutoRole(ListMixin):
    name: str = field()
    content: str = field()
    channel_id: int = field()
    message_id: int = field()
    type: str = field(alias="autorole_type")
    component: dict = field()


@define()
class GuildTag(ListMixin):
    name: str = field()
    title: str = field()
    description: str = field()
    author_id: int = field()
    is_embed: bool = field()
    created_at: int = field()
    last_edited_at: int = field()
    uses_count: int = field()


@define()
class VoiceLobby(DictSerializerMixin):
    channel_id: int = field()
    owner_id: int = field()


@define()
class GuildVoiceLobbies(DataBaseSerializerMixin):
    active_channels: list[VoiceLobby] = field(converter=convert_list(VoiceLobby))
    category_channel_id: int = field()
    voice_channel_id: int = field()
    text_channel_id: int | None = field(default=None)
    private_lobbies: bool = field()

    def get_lobby(self, channel_id: int = None, owner_id: int = None):
        for channel in self.active_channels:
            if channel.channel_id == channel_id or channel.owner_id == owner_id:
                return channel

    def add_channel(self, channel_id: int, owner_id: int) -> VoiceLobby:
        lobby = VoiceLobby(channel_id=channel_id, owner_id=owner_id)
        self.active_channels.append(lobby)
        return lobby

    def remove_lobby(self, channel_id: int = None, owner_id: int = None):
        lobby = self.get_lobby(channel_id=channel_id, owner_id=owner_id)
        self.active_channels.remove(lobby)

    async def update(self):
        key = self._to_database_name(self.__class__.__name__)
        await self._database.update_guild(self.guild_id, key, OperatorType.SET, self.get_changes())


@define()
class GuildLeveling(DataBaseSerializerMixin):
    roles_by_level: dict[int, int] = field(factory=dict)
    voice_factor: int = field(default=10)  # TODO: Add enum for default value
    start_level_role: int = field(default=None)

    async def update(self):
        key = self._to_database_name(self.__class__.__name__)
        await self._database.update_guild(self.guild_id, key, OperatorType.SET, self.get_changes())


@define()
class GuildMessageData(DictSerializerMixin):
    message_id: int = field()
    channel_message_id: int = field()
    users: list[int] = field(factory=list)
    author_id: int = field()

    def add_user(self, user_id: int):
        self.users.append(user_id)

    def remove_user(self, user_id: int):
        self.users.remove(user_id)


@define()
class GuildData(DataBaseSerializerMixin):
    settings: GuildSettings = field(
        converter=GuildSettings,
        add_database=True,
        add_guild_id=True,
        alias="configuration",
        default=None,
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
    voice_lobbies: GuildVoiceLobbies = field(
        converter=GuildVoiceLobbies, default=None, add_guild_id=True, add_database=True
    )
    voice_time: dict[str, int] = field(default=None)
    leveling: GuildLeveling = field(converter=GuildLeveling, default=None)

    async def update(self):
        raise NotImplementedError

    def get_user(self, user_id: int) -> GuildUser | None:
        return next(filter(lambda user: user.id == user_id, self.users), None)

    def get_autorole(self, name: str) -> GuildAutoRole | None:
        return next(filter(lambda autorole: autorole.name == name, self.autoroles), None)

    def get_tag(self, name: str) -> GuildTag | None:
        return next(filter(lambda tag: tag.name == name, self.tags), None)

    async def add_user(self, user_id: int) -> GuildUser:
        return await self._database.add_user(self.guild_id, user_id)

    async def remove_user(self, *, user_id: int = None, user: GuildUser = None):
        await self._database.remove_user(self.guild_id, user_id=user_id, user=user)

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
        return await self._database.add_autorole(
            self.guild_id,
            name=name,
            content=content,
            channel_id=channel_id,
            message_id=message_id,
            type=type,
            component=component,
        )

    async def remove_autorole(self, *, name: str = None, autorole: GuildAutoRole = None):
        await self._database.remove_autorole(self.guild_id, name=name, autorole=autorole)

    async def add_tag(
        self,
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
        return await self._database.add_tag(
            self.guild_id,
            name=name,
            title=title,
            description=description,
            author_id=author_id,
            is_embed=is_embed,
            created_at=created_at,
            last_edited_at=last_edited_at,
            uses_count=uses_count,
        )

    async def remove_tag(self, *, name: str = None, tag: GuildTag = None):
        await self._database.remove_tag(self.guild_id, name=name, tag=tag)
