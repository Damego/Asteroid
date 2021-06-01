import os
from time import sleep

import discord
from discord.ext import commands
from replit import Database, db

from lifetime_alive import keep_alive
from lavalink_server import start_lavalink

if db is not None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)


def get_prefix(bot, message): 
    """Get guild prexif from json """
    return server[str(message.guild.id)]['prefix']


intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# EVENTS
@bot.event
async def on_ready():
    for filename in os.listdir('./extensions'):
        if filename.endswith('.py'):
            bot.load_extension(f'extensions.{filename[:-3]}')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='Чилит'))
    print(f'Бот {bot.user} готов к работе!')

@bot.event
async def on_guild_join(guild):
    server[str(guild.id)] = {
        'prefix':'.',
        'embed_color': 0xFFFFFE,
        'emoji_status': {"online":" ",
                        "dnd":" ",
                        "idle":" ",
                        "offline":" "},
        'users': {},
        'REACTION_POSTS':{}
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

@bot.command(name='reload', help='Перезагрузка плагина', hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    bot.unload_extension(f'extensions.{extension}')
    bot.load_extension(f'extensions.{extension}')
    await ctx.send(f'Плагин {extension} перезагружен!')

@bot.command(name='cmd', description='None', help='None')
@commands.is_owner()
async def custom_command(ctx, *, cmd):
    await eval(cmd)



# ERRORS
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        desc = 'Это команда доступна только владельцу бота!'
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)) and not isinstance(error, commands.MemberNotFound):
        full_desc = f'**Неправильный или потерян аргумент!** \n'
        help = f'`{get_prefix(None, ctx.message)}{ctx.command} {ctx.command.help}`'
        desc = full_desc + help
    elif isinstance(error, commands.ExtensionNotLoaded):
        desc = 'Плагин не загружен'
    elif isinstance(error, commands.ExtensionAlreadyLoaded):
        desc = 'Плагин уже загружен'
    elif isinstance(error, commands.BotMissingPermissions):
        desc = 'У бота недостаточно прав!'
    elif isinstance(error, commands.MissingPermissions):
        desc = 'Недостаточно прав!'
    else:
        desc = f'Произошла ошибка! {error}'

    embed = discord.Embed(description = '❌ '+desc, color=0xff0000)
    await ctx.send(embed=embed)

start_lavalink()
sleep(10)
keep_alive()
bot.run(os.environ['TOKEN'])

