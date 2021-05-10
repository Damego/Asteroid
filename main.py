import random
import json
import discord
from discord.ext import commands
import asyncio
import os
from replit import Database, db
from lifetime_alive import keep_alive

if db != None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)

# JSON PARSE
def get_prefix(bot, message): 
    """Get guild prexif from json """
    return server[str(message.guild.id)]['prefix']


def get_react_post_id():
    """Get guild react post id from json """
    with open('jsons/config.json', 'r') as f:
        token = json.load(f)

    return token["REACTION_POST_ID"]

def get_emoji_role(emoji):
    """Get guild emoji roles from json """
    with open('jsons/roles.json', 'r') as f:
        token = json.load(f)

    return token[f"{emoji}"]

intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# EVENTS
@bot.event
async def on_ready():
    print('Бот {0.user} готов к работе!'.format(bot))
    await change_activity()

for filename in os.listdir('./extensions'):
    if filename.endswith('.py') and not filename.startswith('json_parse'):
        bot.load_extension(f'extensions.{filename[:-3]}')



async def change_activity():
    for i in range(500):
        await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=f'{i+1} вкладку в Pornhub', type=discord.ActivityType.watching))
        await asyncio.sleep(60)
    await change_activity()


@bot.event
async def on_raw_reaction_add(ctx):
    post_id = get_react_post_id()
    if ctx.message_id == post_id:
        emoji = ctx.emoji.id
        role = discord.utils.get(bot.get_guild(ctx.guild_id).roles, id=get_emoji_role(emoji))
        await ctx.member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(ctx):
    post_id = get_react_post_id()
    if ctx.message_id == post_id:
        emoji = ctx.emoji.id
        role = discord.utils.get(bot.get_guild(ctx.guild_id).roles, id=get_emoji_role(emoji))
        guild = bot.get_guild(ctx.guild_id)
        member = await guild.fetch_member(ctx.user_id)
        await member.remove_roles(role)


@bot.event
async def on_member_join(member):
    print(f'{member} Join')

@bot.event
async def on_member_remove(member):
    print(f'{member} Disconnected')

# COMMANDS

@bot.command(name='load', help='Загрузка отдельных модулей', hidden=True)
@commands.is_owner()
async def load(ctx, extension):

    bot.load_extension(f'extensions.{extension}')
    embed = discord.Embed(title=f'Плагин {extension} загружен!')
    await ctx.send(embed=embed)

@bot.command(name='unload', help='Отключение отдельных модулей', hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f'extensions.{extension}')







# ERRORS
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        desc = 'Потерян аргумент!'
    elif isinstance(error, commands.MemberNotFound):
        desc = 'Пользователь не найден!'
    elif isinstance(error, commands.BadArgument):
        desc = 'Неверный аргумент!'
    elif isinstance(error, commands.NotOwner):
        desc = 'Это команда доступна только владельцу бота!'
    else:
        desc = f'Произошла ошибка! {error}'

    embed = discord.Embed(title=desc, color=0xff0000)
    await ctx.send(embed=embed)

keep_alive()
bot.run('ODMzMzQ5MTA5MzQ3Nzc4NTkx.YHxC1g.5mE437ErtMkLpdUAy9PohteRabY') 

