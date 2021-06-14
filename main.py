import os

import discord
from discord.ext import commands

from lifetime_alive import keep_alive

def get_db():
    from replit import Database, db
    if db is not None:
        server = db
    else:
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv('URL')
        server = Database(url)
    return server

def get_prefix(bot, message):
    """Get guild prexif from json """
    prefix = server[str(message.guild.id)]['prefix']
    return commands.when_mentioned_or(prefix)(bot, message)
     
bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all())

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

@bot.command(aliases=['r'],name='reload', help='Перезагрузка плагина', hidden=True)
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
    elif isinstance(error, commands.UserInputError):
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
        desc = str(error)
        if len(desc) == 0:
            desc = 'NO DESCRIPTION FOR THIS ERROR'

    embed = discord.Embed(description = desc, color=0xff0000)
    try:
        await ctx.send(embed=embed)
    except:
        await ctx.send(desc)



if __name__ == '__main__':
    server = get_db()
    #keep_alive()
    bot.run(os.environ['TOKEN'])

