from interactions import Channel, Client, Guild, Member, Message, Role, Snowflake, User
from interactions.ext.i18n import Localization

from .context import CommandContext, ComponentContext
from .database import DataBaseClient

__all__ = ["Asteroid"]


class Asteroid(Client):
    def __init__(self, mongodb_url: str, **kwargs):
        super().__init__(
            command_context=CommandContext, component_context=ComponentContext, **kwargs
        )
        self.database = DataBaseClient(mongodb_url)
        self.i18n = Localization(self)

    # async def send_error(self, exception: Exception, *, guild_id: int | Snowflake = None, channel_id: int | Snowflake = None):
    #     if channel_id is not None:
    #         channel = await self.get_channel(channel_id)
    #     else:
    #         guild = await self.get_guild(guild_id)
    #         if guild.system_channel_id is None:
    #             return  #
    #         channel = await self.get_channel(guild.system_channel_id)

    async def get_guild(self, guild_id: int | Snowflake) -> Guild:
        if guild := self.cache.get_guild(Snowflake(guild_id)):
            return guild

        res = await self._http.get_guild(int(guild_id), with_counts=True)
        return self.cache.add_guild(res)

    async def get_channel(self, channel_id: int | Snowflake) -> Channel:
        if channel := self.cache.get_channel(Snowflake(channel_id)):
            return channel

        res = await self._http.get_channel(channel_id)
        return self.cache.add_channel(res)

    async def get_role(self, guild_id: int | Snowflake, role_id: int | Snowflake) -> Role:
        if role := self.cache.get_role(Snowflake(role_id)):
            return role

        res = await self._http.get_all_roles(int(guild_id))
        self.cache.add_roles(res, Snowflake(guild_id))

        return self.cache.get_role(Snowflake(role_id))

    async def get_message(
        self, channel_id: int | Snowflake, message_id: int | Snowflake
    ) -> Message:
        if message := self.cache.get_message(Snowflake(message_id)):
            return message

        res = await self._http.get_message(int(channel_id), int(message_id))
        return self.cache.add_message(res)

    async def get_user(self, user_id: int | Snowflake) -> User:
        # direct methods are not implemented
        if user := self.cache._get_object(User, Snowflake(user_id)):
            return user

        res = await self._http.get_user(int(user_id))
        return self.cache._add_object(res, User)

    async def get_member(self, guild_id: int | Snowflake, member_id: int | Snowflake) -> Member:
        if member := self.cache.get_member(Snowflake(guild_id), Snowflake(member_id)):
            return member

        res = await self._http.get_member(int(guild_id), int(member_id))
        return self.cache.add_member(res, Snowflake(guild_id))
