import functools
from typing import Coroutine

from discord.ext.commands import MissingPermissions, check, has_guild_permissions
from discord_slash import SlashContext

from .asteroid_bot import AsteroidBot
from .errors import CogDisabledOnGuild, CommandDisabled


def is_administrator_or_bot_owner():
    async def predicate(ctx: SlashContext):
        if ctx.author.guild_permissions.administrator or ctx.author_id == 143773579320754177:
            return True
        raise MissingPermissions(["Administrator"])

    return check(predicate)


def bot_owner_or_permissions(**perms):
    original = has_guild_permissions(**perms).predicate

    async def _check(ctx: SlashContext):
        if ctx.guild is None:
            return False
        return ctx.author.id == 143773579320754177 or await original(ctx)

    return check(_check)


def is_enabled():
    async def predicate(ctx: SlashContext):
        bot: AsteroidBot = ctx.bot
        base = None
        group = None
        name = None
        command_name = bot.get_transformed_command_name(ctx)
        guild_data = await bot.mongo.get_guild_data(ctx.guild_id)

        if guild_data is None:
            return True

        if cog_data := guild_data.cogs_data.get(ctx.cog.name):
            if cog_data.get("disabled", False):
                raise CogDisabledOnGuild

        if not guild_data.configuration.disabled_commands:
            return True

        disabled_commands = guild_data.configuration.disabled_commands
        if command_name in disabled_commands:
            raise CommandDisabled
        command = command_name.split()
        if len(command) == 2:
            base, name = command
        elif len(command) == 3:
            base, group, name = command
        else:
            return True
        if base in disabled_commands:
            raise CommandDisabled
        if group and f"{base} {group}" in disabled_commands:
            raise CommandDisabled
        if name and f"{base} {group} {name}" in disabled_commands:
            raise CommandDisabled

        return True

    return check(predicate)


def cog_is_enabled():
    def wrapper(coro: Coroutine):
        @functools.wraps(coro)
        async def wrapped(self, ctx, *args, **kwargs):
            bot: AsteroidBot = self.bot
            if not ctx.guild:
                return
            guild_data = await bot.mongo.get_guild_data(ctx.guild.id)
            if cog_data := guild_data.cogs_data.get(self.name, {}):
                if cog_data.get("disabled"):
                    return
            return await coro(self, ctx, *args, **kwargs)

        return wrapped

    return wrapper


# No decorator check
async def _cog_is_enabled(self, guild_id: int):
    bot: AsteroidBot = self.bot
    guild_data = await bot.mongo.get_guild_data(guild_id)
    cog_data = guild_data.cogs_data.get(self.name, {})

    if cog_data and cog_data.get("disabled"):
        raise CogDisabledOnGuild
    return True
