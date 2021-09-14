import os
from traceback import format_exception

import discord
from discord.ext import commands
from discord.ext.commands.errors import ExtensionNotLoaded

from extensions import _errors
from mongobot import MongoComponentsBot



def get_prefix(bot, message):
    prefixes = ['a!']
    collection = bot.get_guild_configuration_collection(message.guild.id)
    prefix = collection.find_one({'_id':'configuration'})['prefix']

    if prefix != prefixes[0]:
        prefixes.append(prefix)

    return prefixes


def _load_extensions():
    for filename in os.listdir('./extensions'):
        if not filename.startswith('_'):
            if filename.endswith('.py'):
                bot.load_extension(f'extensions.{filename[:-3]}')
            else:
                bot.load_extension(f'extensions.{filename}')


def _reload_extensions():
    extensions = bot.extensions
    extensions_amount = len(extensions)
    content = ''
    try:
        for count, extension in enumerate(extensions, start=1):
            try:
                bot.reload_extension(extension)
            except Exception as e:
                content += f'\n`{count}/{extensions_amount}. {extension} `❌'
                content += f'\n*Error:* `{e}`'
            else:
                content += f'\n`{count}/{extensions_amount}. {extension} `✅'
    except RuntimeError:
        pass
    return content

intents=discord.Intents.default()
intents.members = True

bot = MongoComponentsBot(command_prefix=get_prefix, intents=intents)


# EVENTS
@bot.event
async def on_ready():
    _load_extensions()
    channel = bot.get_channel(859816092008316928)
    if channel is None:
        channel = await bot.fetch_channel(859816092008316928)
    await channel.send(f'{bot.user} loaded!')

    print(f'{bot.user} loaded!')


@bot.event
async def on_guild_join(guild):
    collection = bot.get_guild_main_collection(guild.id)
    configuration = {
            'prefix':'a!',
            'embed_color': '0xFFFFFE'
    }

    collection['configuration'].update_many(
        {'_id':'configuration'},
        {'$set':configuration},
        upsert=True)


@bot.event
async def on_guild_remove(guild):
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

# COMMANDS
@bot.command(name='load', help='Load an Extension', hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension(f'extensions.{extension}')
    except Exception as e:
        content = f"""
        Extension {extension} not loaded!
        Error: {e}
        """
        await ctx.send(content)
    else:
        await ctx.send(f'Extension {extension} not loaded!')


@bot.command(name='unload', help='Unload Extension', hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension(f'extensions.{extension}')
    except ExtensionNotLoaded:
        await ctx.send(f'Extension {extension} not loaded!')
    else:
        await ctx.send(f'Extension {extension} unloaded!')


@bot.command(aliases=['r'], name='reload', help='Reload Extension', hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.reload_extension(f'extensions.{extension}')
    except Exception as e:
        content = f"""
        Extension {extension} not loaded!
        Error: {e}
        """
        await ctx.send(content)
    else:
        await ctx.message.add_reaction('✅')


@bot.command(aliases=['ra'], name='reload_all', help='Reloading all Extensions', hidden=True)
@commands.is_owner()
async def reload_all(ctx:commands.Context):
    content = _reload_extensions()
    embed = discord.Embed(title='Reloading Extensions', description=content, color=0x2f3136)
    await ctx.send(embed=embed)



# ERRORS
@bot.event
async def on_command_error(ctx:commands.Context, error):
    print(type(error))
    embed = discord.Embed(color=0xED4245)

    if isinstance(error, _errors.TagNotFound):
        desc = 'Tag not found!'
    elif isinstance(error, _errors.ForbiddenTag):
        desc = 'This tag cannot be used!'
    elif isinstance(error, _errors.UIDNotBinded):
        desc = 'You didn\'t tie UID!'
    elif isinstance(error, _errors.GenshinAccountNotFound):
        desc = 'Account with this UID not found!'
    elif isinstance(error, _errors.GenshinDataNotPublic):
        desc = 'Profile is private! Open profile on [site](https://www.hoyolab.com/genshin/accountCenter/gameRecord)'
    elif isinstance(error, commands.NotOwner):
        desc = 'Only owner can use this command!'
    elif isinstance(error, commands.MissingRequiredArgument):
        desc=f'**Missing argument**: `{error.param}`'
    elif isinstance(error, commands.BadArgument):
        title = f'**Bad argument!** \n'
        help = f'`{ctx.prefix}{ctx.command} {ctx.command.help}`'
        desc = title + help
    elif isinstance(error, commands.BotMissingPermissions):
        desc = f'**Bot not have permission for this!**\nRequired permissions: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.MissingPermissions):
        desc = f'**You not have permission for this!**\nRequired permissions: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.CommandNotFound):
        desc = 'Command not found!'
    elif isinstance(error, commands.CommandInvokeError):
        desc = 'Bot don\'t have permission for this!'
    elif isinstance(error, commands.CheckFailure):
        desc = 'You can\'t use this command!'
    else:
        desc = f"""
This bug was sent to owner

*Error:* 
```python
{error}
```
"""
        embed.title = f"""
        ❌ Oops... An unexpected error occurred!
        """

        error_traceback = ''.join(
            format_exception(type(error), error, error.__traceback__)
        )

        error_description = f"""
        **Guild:** {ctx.guild}
        **Channel:** {ctx.channel}
        **User:** {ctx.author}
        **Command:** {ctx.message.content}
        **Error:**
        `{error}`
        **Traceback:**
        ```python
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



if __name__ == '__main__':
    bot.run(os.environ['TOKEN'])

