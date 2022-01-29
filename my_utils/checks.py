from discord.ext.commands import check, MissingPermissions, has_guild_permissions
from discord_slash import SlashContext

from .asteroid_bot import AsteroidBot
from .errors import CogDisabledOnGuild, CommandDisabled


def is_administrator_or_bot_owner():
    async def predicate(ctx: SlashContext):
        if (
            ctx.author.guild_permissions.administrator
            or ctx.author_id == 143773579320754177
        ):
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
        collection = bot.get_guild_main_collection(ctx.guild_id)
        guild_data = collection.find_one({"_id": "configuration"})
        if guild_data is None:
            return True
        if not guild_data.get("disabled_commands"):
            return True
        disabled_commands = guild_data["disabled_commands"]
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


def cog_is_enabled(func):
    async def wrapper(self, ctx: SlashContext, **kwargs):
        bot: AsteroidBot = self.bot
        collection = bot.get_guild_main_collection(ctx.guild_id)
        try:
            enabled = collection.find_one({"_id": "cogs_status"})[self.name]
        except Exception:
            enabled = True
        if not enabled:
            raise CogDisabledOnGuild
        if not kwargs:
            return await func(self, ctx)
        return await func(self, ctx, **kwargs)

    return wrapper


# No decorator check
def _cog_is_enabled(self, guild_id: int):
    bot: AsteroidBot = self.bot
    collection = bot.get_guild_main_collection(guild_id)
    try:
        enabled = collection.find_one({"_id": "cogs_status"})[self.name]
    except Exception:
        enabled = True
    if not enabled:
        raise CogDisabledOnGuild
    return enabled
