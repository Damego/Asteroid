import logging
from os import listdir, environ
from traceback import format_exception

from discord import Guild, Intents, Embed
from discord.ext import commands
from discord_slash_components_bridge import SlashCommand

from my_utils import AsteroidBot, get_content
from my_utils.errors import *
from my_utils import slash_override



def _load_extensions():
    for filename in listdir('./cogs'):
        if not filename.startswith('_'):
            if filename.endswith('.py'):
                bot.load_extension(f'cogs.{filename[:-3]}')
            else:
                bot.load_extension(f'cogs.{filename}')


bot = AsteroidBot(
    command_prefix='+',
    intents=Intents.all()
)
slash = SlashCommand(bot, sync_commands=False, sync_on_cog_reload=True)

# EVENTS
@bot.event
async def on_ready():
    channel = bot.get_channel(891222610166284368)
    if channel is None:
        channel = await bot.fetch_channel(891222610166284368)
    await channel.send(f'{bot.user} успешно загружен!')

    print(f'{bot.user} загружен!')


@bot.event
async def on_guild_join(guild: Guild):
    collection = bot.get_guild_main_collection(guild.id)
    configuration = {
        'embed_color': '0xFFFFFE'
    }

    collection['configuration'].update_one(
        {'_id':'configuration'},
        {'$set':configuration},
        upsert=True
    )


@bot.event
async def on_guild_remove(guild: Guild):
    return
    guild_id = guild.id
    collections = [
        bot.get_guild_main_collection(guild_id),
        bot.get_guild_configuration_collection(guild_id),
        bot.get_guild_level_roles_collection(guild_id),
        bot.get_guild_reaction_roles_collection(guild_id),
        bot.get_guild_tags_collection(guild_id),
        bot.get_guild_users_collection(guild_id),
        bot.get_guild_voice_time_collection(guild_id),
    ]

    for collection in collections:
        collection.drop()


@bot.event
async def on_slash_command_error(ctx, error):
    print(error)
    embed = Embed(color=0xED4245)
    lang = bot.get_guild_bot_lang(ctx.guild_id)
    content = get_content('ERRORS_DESCRIPTIONS', lang)

    if isinstance(error, CogDisabledOnGuild):
        desc = content['COG_DISABLED']
    elif isinstance(error, TagNotFound):
        desc = content['TAG_NOT_FOUND']
    elif isinstance(error, ForbiddenTag):
        desc = content['FORBIDDEN_TAG']
    elif isinstance(error, NotTagOwner):
        desc = content['NOT_TAG_OWNER']
    elif isinstance(error, UIDNotBinded):
        desc = content['UID_NOT_BINDED']
    elif isinstance(error, GenshinAccountNotFound):
        desc = content['GI_ACCOUNT_NOT_FOUND']
    elif isinstance(error, GenshinDataNotPublic):
        desc = content['GI_DATA_NOT_PUBLIC']
    elif isinstance(error, NotConnectedToVoice):
        desc = content['NOT_CONNECTED_TO_VOICE']
    elif isinstance(error, commands.NotOwner):
        desc = content['NOT_BOT_OWNER']
    elif isinstance(error, commands.BotMissingPermissions):
        desc = f'**Bot don\'t have permission for this!**\nRequired permissions: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.MissingPermissions):
        desc = f'**You don\'t have permission for this!**\nRequired permissions: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.CheckFailure):
        desc = content['CHECK_FAILURE']
    else:
        desc = content['OTHER_ERRORS_DESCRIPTION'].format(error=error)
        embed.title = content['OTHER_ERRORS_TITLE']

        error_traceback = ''.join(
            format_exception(type(error), error, error.__traceback__)
        )

        error_description = f"""
        **Guild:** {ctx.guild}
        **Channel:** {ctx.channel}
        **User:** {ctx.author}
        **Error:**
        `{error}`
        **Traceback:**
        ``` \n
        {error_traceback}
        ``` """

        channel = ctx.bot.get_channel(863001051523055626)
        if channel is None:
            channel = await ctx.bot.fetch_channel(863001051523055626)
        try:
            await channel.send(error_description)
        except Exception:
            await channel.send('Произошла ошибка! Чекни логи!')
            print(error_description)

    embed.description = desc
    try:
        await ctx.send(embed=embed)
    except:
        await ctx.send(desc)



_load_extensions()
bot.run(environ.get('BOT_TOKEN'))