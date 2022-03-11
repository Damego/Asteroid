from os import getenv
from datetime import datetime
from traceback import *
from sys import exc_info

from discord import Guild, Intents, Embed, Forbidden
from discord.ext.commands import NotOwner, BotMissingPermissions, MissingPermissions, CheckFailure, BadArgument
from discord_slash import SlashContext
from dotenv import load_dotenv
from genshin.errors import DataNotPublic, AccountNotFound

from my_utils import AsteroidBot, get_content, transform_permission, consts
from my_utils.errors import *
from my_utils import slash_override

bot = AsteroidBot(command_prefix="+", intents=Intents.all())


# EVENTS
@bot.event
async def on_ready():
    channel = bot.get_channel(891222610166284368)
    if channel is None:
        channel = await bot.fetch_channel(891222610166284368)
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
    embed = Embed(color=0xED4245)
    lang = await bot.get_guild_bot_lang(ctx.guild_id)
    content = get_content("ERRORS_DESCRIPTIONS", lang)

    if isinstance(error, CogDisabledOnGuild):
        desc = content["COG_DISABLED"]
    elif isinstance(error, CommandDisabled):
        desc = content["COMMAND_DISABLED"]
    elif isinstance(error, NoData):
        desc = content["NO_DATA_FOUND"]
    elif isinstance(error, TagNotFound):
        desc = content["TAG_NOT_FOUND"]
    elif isinstance(error, ForbiddenTag):
        desc = content["FORBIDDEN_TAG"]
    elif isinstance(error, NotTagOwner):
        desc = content["NOT_TAG_OWNER"]
    elif isinstance(error, UIDNotBinded):
        desc = content["UID_NOT_BINDED"]
    elif isinstance(error, AccountNotFound):
        desc = content["GI_ACCOUNT_NOT_FOUND"]
    elif isinstance(error, DataNotPublic):
        desc = content["GI_DATA_NOT_PUBLIC"]
    elif isinstance(error, BotNotConnectedToVoice):
        desc = content["BOT_NOT_CONNECTED"]
    elif isinstance(error, NotConnectedToVoice):
        desc = content["NOT_CONNECTED_TO_VOICE_TEXT"]
    elif isinstance(error, NotPlaying):
        desc = content["NOT_PLAYING"]
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

        error_traceback = "".join(
            format_exception(type(error), error, error.__traceback__)
        )

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
                name="Channel", value=f"Name: `{ctx.channel.name}`\n ID:`{ctx.channel_id}`"
            )
        error_embed.add_field(
            name="User", value=f"Name: `{ctx.author.name}`\n ID:`{ctx.author_id}`"
        )
        error_embed.add_field(name="Short Description", value=f"`{error}`")
        channel = ctx.bot.get_channel(863001051523055626)
        if channel is None:
            channel = await ctx.bot.fetch_channel(863001051523055626)
        try:
            await channel.send(embed=error_embed)
        except Exception:
            error_embed.description = "Checks logs"
            await channel.send(embed=error_embed)
            print(error_traceback)

    embed.description = desc
    try:
        await ctx.send(embed=embed)
    except:
        await ctx.send(desc)


load_dotenv()
bot.run(getenv("BOT_TOKEN"))
