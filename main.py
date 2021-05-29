import os
import asyncio

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
    print(f'Бот {bot.user} готов к работе!')
    await change_activity()

async def change_activity():
    for i in range(500):
        await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=f'{i+1} вкладку в Pornhub', type=discord.ActivityType.watching))
        await asyncio.sleep(60)
    await change_activity()

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


# ERRORS
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        desc = f'Потерян аргумент!'
    elif isinstance(error, commands.MemberNotFound):
        desc = 'Пользователь не найден!'
    elif isinstance(error, commands.BadArgument):
        desc = 'Неправильно задан аргумент!'
    elif isinstance(error, commands.NotOwner):
        desc = 'Это команда доступна только владельцу бота!'
    else:
        desc = f'Произошла ошибка! {error}'

    embed = discord.Embed(title=desc, color=0xff0000)
    await ctx.send(embed=embed)

start_lavalink()
keep_alive()
bot.run(os.environ['TOKEN'])

