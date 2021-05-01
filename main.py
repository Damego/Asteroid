import random
import json
import discord
from discord.ext import commands
import qrcode
import asyncio
import os

# JSON PARSE
def get_prefix(bot, message): 
    """Get guild prexif from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)

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


def get_stats(message, member):
    """Get guild members stats from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)
    ls = {
        'xp':server[str(message.guild.id)]['users'][str(member.id)]['xp'],
        'lvl':server[str(message.guild.id)]['users'][str(member.id)]['level']
        }
    return ls


def get_emoji_status(message):
    """Get guild emoji status for stats from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)
    ls = {
        'online':server[str(message.guild.id)]['emoji_status']['online'],
        'dnd':server[str(message.guild.id)]['emoji_status']['dnd'],
        'idle':server[str(message.guild.id)]['emoji_status']['idle'],
        'offline':server[str(message.guild.id)]['emoji_status']['offline'],
        }
    return ls


def get_embed_color(message):
    """Get color for embeds from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)

    return int(server[str(message.guild.id)]['embed_color'], 16)





intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.remove_command('help')


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

@bot.command(name='unload', help='Выгрузка отдельных модулей', hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f'extensions.{extension}')


@bot.command(aliases=['реши'])
async def exercise(ctx, arg): # Решает простой матемаический пример
    exercise = arg
    try:
        exercise = eval(exercise)
        await ctx.send(exercise)
    except Exception:
        await ctx.send('Указаны неверные числа/действие!!!')
    

@bot.command(aliases=['рандом'], name='random')
async def random_num(ctx, arg1, arg2): # Выдаёт рандомное число в заданном промежутке
    arg1 = int(arg1)
    arg2 = int(arg2)
    num = random.randint(arg1,arg2)
    await ctx.reply(f'Рандомное число: {num}')


@bot.command(aliases=['инфо'])
async def info(ctx, *, member: discord.Member): # Выводит информацию об участнике канала
    embed = discord.Embed(title=f'Информация о пользователе {member}', color = get_embed_color(ctx.message))

    stats = get_stats(ctx.message, member)
    lvl = stats['lvl']
    xp = stats['xp']

    member_roles_names = []
    for role in member.roles:
        member_roles_names.append(role.name)
    member_roles_names = ', '.join(member_roles_names)

    ls = get_emoji_status(ctx.message)
    member_status = str(member.status)
    if member_status == 'online':
        member_status = '{} В сети'.format(ls['online'])
    elif member_status == 'dnd':
        member_status = '{} Не беспокоить'.format(ls['dnd'])
    elif member_status == 'idle':
        member_status = '{} Не активен'.format(ls['idle'])
    elif member_status == 'offline':
        member_status = '{} Не в сети'.format(ls['offline'])

    embed.add_field(name= "Основная информация:" ,value=f"""
        **Дата регистрации в Discord:** {member.created_at.strftime("%#d %B %Y")}
        **Дата присоединения на сервер:** {member.joined_at.strftime("%#d %B %Y")}
        **Текущий статус:** {member_status}
        **Роли:** {member_roles_names}
        """, inline=False)

    embed.add_field(name='Уровень:', value=lvl)
    embed.add_field(name='Опыт:', value=xp)

    embed.set_thumbnail(url=member.avatar_url)
    await ctx.send(embed=embed)


@commands.has_guild_permissions(administrator=True)
@bot.command(aliases=['префикс'])
async def changeprefix(ctx, prefix): # Меняет префикс у команд
        with open('jsons/servers.json', 'r') as f:
            server = json.load(f)

        server[str(ctx.guild.id)]['prefix'] = prefix

        with open('jsons/servers.json', 'w') as f:
            json.dump(server, f, indent=4)

        embed = discord.Embed(title=f'Префикс команд поменялся на {prefix}')
        await ctx.send(embed=embed)


@bot.command(name='qr', aliases=['QR', 'код'])
async def create_qr(ctx, *, text):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1
    )
    qr.add_data(data=text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f'./qrcodes/{ctx.message.author.id}.png')
    await ctx.send(file = discord.File(f'./qrcodes/{ctx.message.author.id}.png'))
    os.remove(f'./qrcodes/{ctx.message.author.id}.png')

@bot.command(aliases=['e_color', 'цвет'])
@commands.has_guild_permissions(administrator=True)
async def change_embed_color(ctx, new_color):
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)
        server[str(ctx.guild.id)]['embed_color'] = '0x'+new_color
    
    with open('jsons/servers.json', 'w') as f:
        json.dump(server, f, indent=4)

@bot.command(aliases=['записать_сервер'])
@commands.is_owner() 
async def add_guild_in_json(guild): # Если в файле не прописан сервер, то это команда прописывает
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)

    server[str(guild.id)] = {
        'prefix':'.',
        "embed_color": "0xFFFFFE",
        'emoji_status': {},
        'users': {}
    }

    with open('jsons/servers.json', 'w') as f:
        json.dump(server, f, indent=4)

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


bot.run('ODMzMzQ5MTA5MzQ3Nzc4NTkx.YHxC1g.HrQIqoym_SRJXF2Zha1kJbdJtJY')

