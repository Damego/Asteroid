from datetime import datetime
from os import getenv
from traceback import format_exception

from discord import Embed, Forbidden, Guild, Intents
from discord.ext.commands import (
    BadArgument,
    BotMissingPermissions,
    CheckFailure,
    MissingPermissions,
    NotOwner,
)
from discord_slash import SlashContext
from dotenv import load_dotenv
from genshin.errors import AccountNotFound, DataNotPublic

from utils import (  # noqa: F401
    AsteroidBot,
    DiscordColors,
    SystemChannels,
    errors,
    get_content,
    slash_override,
    transform_permission,
)

bot = AsteroidBot(command_prefix="asteroid!", intents=Intents.all())


# EVENTS
@bot.event
async def on_ready():
    channel = bot.get_channel(SystemChannels.BOT_UPTIME_CHANNEL)
    if channel is None:
        channel = await bot.fetch_channel(SystemChannels.BOT_UPTIME_CHANNEL)
    await channel.send(f"{bot.user} успешно загружен!")

    print(f"{bot.user} загружен!")


@bot.event
async def on_guild_join(guild: Guild):
    await bot.mongo.add_guild(guild.id)


@bot.event
async def on_guild_remove(guild: Guild):
    await bot.mongo.delete_guild(guild.id)


@bot.listen(name="on_slash_command_error")
async def on_slash_command_error(ctx: SlashContext, error):
    embed = Embed(color=DiscordColors.RED)
    if ctx.guild is None:
        lang = "English"
    else:
        lang = await bot.get_guild_bot_lang(ctx.guild_id)
    content = get_content("ERRORS_DESCRIPTIONS", lang)

    if isinstance(error, errors.CogDisabledOnGuild):
        desc = content["COG_DISABLED"]
    elif isinstance(error, errors.CommandDisabled):
        desc = content["COMMAND_DISABLED"]
    elif isinstance(error, errors.NoData):
        desc = content["NO_DATA_FOUND"]
    elif isinstance(error, errors.TagNotFound):
        desc = content["TAG_NOT_FOUND"]
    elif isinstance(error, errors.ForbiddenTag):
        desc = content["FORBIDDEN_TAG"]
    elif isinstance(error, errors.NotTagOwner):
        desc = content["NOT_TAG_OWNER"]
    elif isinstance(error, errors.UIDNotBinded):
        desc = content["UID_NOT_BINDED"]
    elif isinstance(error, AccountNotFound):
        desc = content["GI_ACCOUNT_NOT_FOUND"]
    elif isinstance(error, DataNotPublic):
        desc = content["GI_DATA_NOT_PUBLIC"]
    elif isinstance(error, errors.BotNotConnectedToVoice):
        desc = content["BOT_NOT_CONNECTED"]
    elif isinstance(error, errors.NotConnectedToVoice):
        desc = content["NOT_CONNECTED_TO_VOICE_TEXT"]
    elif isinstance(error, errors.NotPlaying):
        desc = content["NOT_PLAYING"]
    elif isinstance(error, errors.NotGuild):
        desc = content["GUILD_ONLY"]
    elif isinstance(error, errors.PrivateVoiceNotSetup):
        desc = content["PRIVATE_VOICE_NOT_SETUP"]
    elif isinstance(error, errors.DontHavePrivateRoom):
        desc = content["DONT_HAVE_PRIVATE_ROOM"]
    elif isinstance(error, NotOwner):
        desc = content["NOT_BOT_OWNER"]
    elif isinstance(error, BotMissingPermissions):
        missing_perms = [transform_permission(perm) for perm in error.missing_perms]
        desc = f'{content["BOT_DONT_HAVE_PERMS"]} `{", ".join(missing_perms)}`'
    elif isinstance(error, MissingPermissions):
        missing_perms = [transform_permission(perm) for perm in error.missing_perms]
        desc = f'{content["DONT_HAVE_PERMS"]} `{", ".join(missing_perms)}`'
    elif isinstance(error, CheckFailure):
        desc = content["CHECK_FAILURE"]
    elif isinstance(error, BadArgument):
        desc = content["BAD_ARGUMENT"]
    elif isinstance(error, Forbidden):
        desc = content["FORBIDDEN"]
    else:
        desc = content["OTHER_ERRORS_DESCRIPTION"].format(error=error)
        embed.title = content["OTHER_ERRORS_TITLE"]

        error_traceback = "".join(format_exception(type(error), error, error.__traceback__))

        error_embed = Embed(
            title="Unexpected error",
            description=f"``` {error_traceback} ```",
            timestamp=datetime.utcnow(),
            color=0xED4245,
        )
        error_embed.add_field(
            name="Command Name", value=f"`/{bot.get_transformed_command_name(ctx)}`"
        )
        if ctx.guild is not None:
            error_embed.add_field(
                name="Guild", value=f"Name: `{ctx.guild.name}`\n ID:`{ctx.guild_id}`"
            )
            error_embed.add_field(
                name="Channel",
                value=f"Name: `{ctx.channel.name}`\n ID:`{ctx.channel_id}`",
            )
        error_embed.add_field(
            name="User", value=f"Name: `{ctx.author.name}`\n ID:`{ctx.author_id}`"
        )
        error_embed.add_field(name="Short Description", value=f"`{error}`")
        channel = ctx.bot.get_channel(SystemChannels.ERRORS_CHANNEL)
        if channel is None:
            channel = await ctx.bot.fetch_channel(SystemChannels.ERRORS_CHANNEL)
        try:
            await channel.send(embed=error_embed)
        except Exception:
            error_embed.description = "Checks logs"
            await channel.send(embed=error_embed)
            print(error_traceback)

    embed.description = desc
    try:
        await ctx.send(embed=embed)
    except Exception:
        await ctx.send(desc)


load_dotenv()
bot.run(getenv("BOT_TOKEN"))
