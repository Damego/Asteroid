from functools import wraps

from interactions import (
    Channel,
    Guild,
    LibraryException,
    Member,
    Message,
    Role,
    Snowflake,
    User,
    get,
)
from interactions.ext.lavalink import VoiceClient

from .database import DataBaseClient
from .locale import Locale, LocaleManager

__all__ = ["Asteroid"]


class Asteroid(VoiceClient):
    def __init__(self, bot_token: str, mongodb_url: str, **kwargs):
        super().__init__(bot_token, **kwargs)
        self.database = DataBaseClient(mongodb_url)
        self.locale = LocaleManager("locale")

    async def get_locale(self, guild_id: int | Snowflake) -> Locale:
        guild_data = await self.database.get_guild(
            int(guild_id) if isinstance(guild_id, Snowflake) else guild_id
        )
        return self.locale[guild_data.settings.language]

    async def try_run(self, func, *args, **kwargs):
        """
        Tries to run async function and nothing does if got exception
        """
        try:
            return await func(*args, **kwargs)
        except LibraryException:
            pass

    @wraps(get)
    def get(self, *args, **kwargs):
        return get(self, *args, **kwargs)

    # Aliases to `get` function
    async def get_guild(self, guild_id: int | Snowflake) -> Guild:
        return await get(self, Guild, object_id=int(guild_id))

    async def get_channel(self, channel_id: int | Snowflake) -> Channel:
        return await get(self, Channel, object_id=int(channel_id))

    async def get_role(self, guild_id: int | Snowflake, role_id: int | Snowflake) -> Role:
        return await get(self, Role, parent_id=int(guild_id), object_id=int(role_id))

    async def get_message(
        self, channel_id: int | Snowflake, message_id: int | Snowflake
    ) -> Message:
        return await get(self, Message, parent_id=int(channel_id), object_id=int(message_id))

    async def get_user(self, user_id: int | Snowflake) -> User:
        return await get(self, User, object_id=int(user_id))

    async def get_member(self, guild_id: int | Snowflake, member_id: int | Snowflake) -> Member:
        return await get(self, Member, parent_id=int(guild_id), object_id=int(member_id))
