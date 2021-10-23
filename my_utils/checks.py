from typing import Union

from discord import RawReactionActionEvent
from discord.ext.commands import check, MissingPermissions
from discord_slash import SlashContext

from .asteroid_bot import AsteroidBot
from .errors import CogDisabledOnGuild

def is_administrator_or_bot_owner():
    async def predicate(ctx: SlashContext):
        if ctx.author.guild_permissions.administrator or ctx.author_id == 143773579320754177:
            return True
        raise MissingPermissions(['Administrator'])
    return check(predicate)


def is_enabled(func):
    async def wrapper(self, ctx: SlashContext, **kwargs):
        bot: AsteroidBot = self.bot
        collection = bot.get_guild_configuration_collection(ctx.guild_id)
        try:
            enabled = collection.find_one({'_id': 'cogs_status'})[self.name]
        except KeyError:
            enabled = True
        if not enabled:
            raise CogDisabledOnGuild
        if not kwargs:
            return await func(self, ctx)
        return await func(self, ctx, **kwargs)

    return wrapper

# No decorator check
def _is_enabled(self, guild_id: int):
    bot: AsteroidBot = self.bot
    collection = bot.get_guild_configuration_collection(guild_id)
    try:
        enabled = collection.find_one({'_id': 'cogs_status'})[self.name]
    except KeyError:
        enabled = True
    if not enabled:
        raise CogDisabledOnGuild