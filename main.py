import os
from traceback import format_exception
from pymongo import MongoClient

import discord
from discord.ext import commands
from discord.ext.commands.errors import ExtensionNotLoaded, ExtensionAlreadyLoaded
from discord_components import DiscordComponents

from extensions import _errors

def get_db1():
    from replit import Database, db
    if db is not None:
        return db
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('REPLIT_DB_URL')
    return Database(url)

def get_collection(guild_id):
    cluster = MongoClient(os.getenv('MONGODB_URL'))
    guilds = cluster['guilds']
    return guilds[str(guild_id)]

def get_prefix(bot, message):
    """Get guild prexif from json """
    try:
        collection = get_collection(message.guild.id)
        prefix = collection.find_one({'_id':'configuration'})['prefix']
    except Exception as e:
        print('CANT GET PREFIX! ERROR:', e)
        prefix = 'a!'

    return prefix

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
                content += f'\n*Ошибка:* `{e}`'
            else:
                content += f'\n`{count}/{extensions_amount}. {extension} `✅'
    except RuntimeError:
        pass
    return content


bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all())

# EVENTS
@bot.event
async def on_ready():
    _load_extensions()
    DiscordComponents(bot)
    print(f'Бот {bot.user} готов к работе!')


@bot.event
async def on_guild_join(guild):
    collection = get_collection(guild.id)
    configuration = {
            'prefix':'a!',
            'embed_color': '0xFFFFFE'
    }

    collection.update_one(
        {'_id':'configuration'},
        {'$set':configuration},
        upsert=True)

    collection.update_one(
        {'_id':'reaction_posts'},
        {'$set':{}},
        upsert=True)

    collection.update_one(
        {'_id':'tags'},
        {'$set':{}},
        upsert=True)

    collection.update_one(
        {'_id':'voice_time'},
        {'$set':{}},
        upsert=True)

    collection.update_one(
        {'_id':'users'},
        {'$set':{}},
        upsert=True)


@bot.command()
@commands.is_owner()
async def full_clear_guild_db(ctx):
    server[str(ctx.guild.id)] = {
        'roles_by_level':{},
        'users': {},
        'reaction_posts':{},
        'tags':{},
        'voice_time':{}
    }


@bot.event
async def on_guild_remove(guild):
    collection = get_collection(guild.id)
    collection.drop()

# COMMANDS
@bot.command(name='load', help='Загрузка плагина', hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension(f'extensions.{extension}')
    except Exception as e:
        content = f"""
        Расширение {extension} не загружено!
        Ошибка: {e}
        """
        await ctx.send(content)
    else:
        await ctx.send(f'Плагин {extension} загружен!')


@bot.command(name='unload', help='Отключение плагина', hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension(f'extensions.{extension}')
    except ExtensionNotLoaded:
        await ctx.send(f'Плагин {extension} не загружен')
    else:
        await ctx.send(f'Плагин {extension} отключен!')


@bot.command(aliases=['r'], name='reload', help='Перезагрузка плагина', hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.reload_extension(f'extensions.{extension}')
    except Exception as e:
        content = f"""
        Расширение {extension} не загружено!
        Ошибка: {e}
        """
        await ctx.send(content)
    else:
        await ctx.message.add_reaction('✅')


@bot.command(aliases=['ra'], name='reload_all', help='Перезагрузка всех плагинов', hidden=True)
@commands.is_owner()
async def reload_all(ctx:commands.Context):
    content = _reload_extensions()
    embed = discord.Embed(title='Перезагрузка расширений', description=content, color=0x2f3136)
    await ctx.send(embed=embed)


@bot.command(name='cmd', description='None', help='None')
@commands.is_owner()
async def custom_command(ctx, *, cmd):
    await eval(cmd)


@bot.command(name='deploy')
@commands.is_owner()
async def git_pull_updates(ctx:commands.Context):
    embed = discord.Embed(title='Загрузка обновления...', color=0x2f3136)
    await ctx.send(embed=embed)
    os.system('git fetch')
    os.system('git stash')
    os.system('git pull')

    content = _reload_extensions()
    embed = discord.Embed(title='Перезагрузка расширений...', description=content, color=0x2f3136)
    await ctx.send(embed=embed)


# ERRORS
@bot.event
async def on_command_error(ctx:commands.Context, error):
    embed = discord.Embed(color=0xED4245)

    if isinstance(error, _errors.TagNotFound):
        desc = 'Тег не найден!'
    elif isinstance(error, _errors.ForbiddenTag):
        desc = 'Этот тег нельзя использовать!'
    elif isinstance(error, _errors.UIDNotBinded):
        desc = 'У вас не привязан UID!'
    elif isinstance(error, _errors.GenshinAccountNotFound):
        desc = 'Аккаунт с таким UID не найден! Похоже вы ввели неверный UID.'
    elif isinstance(error, _errors.GenshinDataNotPublic):
        desc = 'Профиль закрыт! Откройте профиль на [сайте](https://www.hoyolab.com/genshin/accountCenter/gameRecord)'
    elif isinstance(error, commands.NotOwner):
        desc = 'Это команда доступна только владельцу бота!'
    elif isinstance(error, commands.MissingRequiredArgument):
        desc=f'**Потерян аргумент**: `{error.param}`'
    elif isinstance(error, commands.BadArgument):
        title = f'**Неправильный аргумент!** \n'
        help = f'`{get_prefix(bot, ctx.message)[2]}{ctx.command} {ctx.command.help}`'
        desc = title + help
    elif isinstance(error, commands.BotMissingPermissions):
        desc = f'**У меня недостаточно прав!**\nНеобходимые права: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.MissingPermissions):
        desc = f'**У вас недостаточно прав!**\nНеобходимые права: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.CommandNotFound):
        desc = 'Команда не найдена!'
    else:
        desc = f"""
Я уже уведомил своего создателя об этой ошибке

*Ошибка:* 
```python
{error}
```
"""
        embed.title = f"""
        ❌ Упс... Произошла непредвиденная ошибка!
        """

        error_traceback = ''.join(
            format_exception(type(error), error, error.__traceback__)
        )

        error_description = f"""
        **Сервер:** {ctx.guild}
        **Канал:** {ctx.channel}
        **Пользователь:** {ctx.author}
        **Команда:** {ctx.message.content}
        **Ошибка:**
        `{error}`
        **Лог ошибки:**
        ```python
        {error_traceback}
        ``` """

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

