import os
from traceback import format_exception

import discord
from discord.ext import commands
from discord_components import DiscordComponents

from extensions import _errors
from lifetime_alive import keep_alive

def get_db():
    from replit import Database, db
    if db is not None:
        return db
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    return Database(url)

def get_prefix(bot, message):
    """Get guild prexif from json """
    try:
        prefix = server[str(message.guild.id)]['configuration']['prefix']
    except KeyError:
        prefix = 'a!'

    return prefix


bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all())

# EVENTS
@bot.event
async def on_ready():
    for filename in os.listdir('./extensions'):
        if (not filename.startswith('_')) and filename.endswith('.py'):
            bot.load_extension(f'extensions.{filename[:-3]}')
    DiscordComponents(bot)
    print(f'Бот {bot.user} готов к работе!')


@bot.event
async def on_guild_join(guild):
    server[str(guild.id)] = {
        'configuration':{
            'prefix':'!d',
            'embed_color': '0xFFFFFE',
            'extensions':{
                'Games': True,
                'HLTV': True,
                'Levels': True,
                'Misc': True,
                'Moderation': True,
                'ReactionRole': True,
                'Tags': True,
                'ButtonMusic': True,
                'Music': True,
            }
        },
        'roles_by_level':{},
        'users': {},
        'reaction_posts':{},
        'tags':{},
        'voice_time':{}
    }


@bot.command()
@commands.is_owner()
async def full_clear_guild_db(ctx):
    server[str(ctx.guild.id)] = {
        'configuration':{
            'prefix':'!d',
            'embed_color': '0xFFFFFE',
            'extensions':{
                'Games': True,
                'HLTV': True,
                'Levels': True,
                'Misc': True,
                'Moderation': True,
                'ReactionRole': True,
                'Tags': True,
                'ButtonMusic': True,
                'Music': True,
            }
        },
        'roles_by_level':{},
        'users': {},
        'reaction_posts':{},
        'tags':{},
        'voice_time':{}
    }


@bot.command()
@commands.is_owner()
async def clear_guild_settings(ctx):
    server[str(ctx.guild.id)] = {
        'configuration':{
            'prefix':'!d',
            'embed_color': '0xFFFFFE',
            'extensions':{
                'Games': True,
                'HLTV': True,
                'Levels': True,
                'Misc': True,
                'Moderation': True,
                'ReactionRole': True,
                'Tags': True,
                'NewMusic': True,
            }
        }
    }


@bot.event
async def on_guild_remove(guild):
    server.pop(str(guild.id))

# COMMANDS
@bot.command(name='load', help='Загрузка плагина', hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f'extensions.{extension}')
    await ctx.send(f'Плагин {extension} загружен!')


@bot.command(name='unload', help='Отключение плагина', hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f'extensions.{extension}')
    await ctx.send(f'Плагин {extension} отключен!')


@bot.command(aliases=['r'], name='reload', help='Перезагрузка плагина', hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    bot.reload_extension(f'extensions.{extension}')
    await ctx.message.add_reaction('✅')


@bot.command(aliases=['ra'], name='reload_all', help='Перезагрузка всех плагинов', hidden=True)
@commands.is_owner()
async def reload_all(ctx):
    extensions = bot.extensions
    try:
        for count, extension in enumerate(extensions, start=1):
            bot.reload_extension(extension)
            print(f'{count}/{len(extensions)}. {extension} was reloaded!')
    except RuntimeError:
        pass

    await ctx.message.add_reaction('✅')


@bot.command(name='cmd', description='None', help='None')
@commands.is_owner()
async def custom_command(ctx, *, cmd):
    await eval(cmd)


# ERRORS
@bot.event
async def on_command_error(ctx:commands.Context, error):
    embed = discord.Embed(color=0xED4245)
    if isinstance(error, _errors.TagNotFound):
        desc = 'Тег не найден!'
    elif isinstance(error, _errors.ForbiddenTag):
        desc = 'Этот тег нельзя использовать!'
    elif isinstance(error, commands.NotOwner):
        desc = 'Это команда доступна только владельцу бота!'
    elif isinstance(error, commands.MissingRequiredArgument):
        desc=f'**Потерян аргумент**: `{error.param}`'
    elif isinstance(error, commands.BadArgument):
        title = f'**Неправильный аргумент!** \n'
        help = f'`{get_prefix(bot, ctx.message)[2]}{ctx.command} {ctx.command.help}`'
        desc = title + help
    elif isinstance(error, commands.ExtensionNotLoaded):
        desc = 'Плагин не загружен'
    elif isinstance(error, commands.ExtensionAlreadyLoaded):
        desc = 'Плагин уже загружен'
    elif isinstance(error, commands.BotMissingPermissions):
        desc = f'**У меня недостаточно прав!**\nНеобходимые права: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.MissingPermissions):
        desc = f'**У вас недостаточно прав!**\nНеобходимые права: `{", ".join(error.missing_perms)}`'
    elif isinstance(error, commands.CommandNotFound):
        desc = 'Команда не найдена!'
    else:
        desc = f'Я уже уведомил своего создателя об этой ошибке\n*Ошибка:* `{error}`'
        embed.title = f"""
        ❌ Упс... Произошла непредвиденная ошибка!
        """

        error_description = f"""**Сервер:** {ctx.guild}\n**Канал:** {ctx.channel}\n**Пользователь:** {ctx.author}\n**Команда:** {ctx.message.content}
**Ошибка:**
`{error}`
**Лог ошибки:**
```python
{format_exception(type(error), error, error.__traceback__)}
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
    server = get_db()
    keep_alive()
    bot.run(os.environ['TOKEN'])

