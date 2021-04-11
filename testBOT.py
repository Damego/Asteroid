import random
import json
import discord
from discord.ext import commands
import asyncio
import os

userhelp = open('help.txt', encoding='UTF-8')

def get_prefix(bot, message): 
    with open('jsons/prefixes.json', 'r') as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]

def get_token(): 
    with open('jsons/config.json', 'r') as f:
        token = json.load(f)

    return token["TOKEN"]

TOKEN = get_token()
bot = commands.Bot(command_prefix=get_prefix)
bot.remove_command('help')
@bot.group(invoke_without_command=True)
async def help(ctx):
    cprefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title='Справочник команд', color=0xff0800)
    embed.add_field(name='Музыка', value=f'`{cprefix}help music || музыка`', inline=False)
    embed.add_field(name='Модерация', value=f'`{cprefix}help moderation || модерация`', inline=False)
    embed.add_field(name='Разное', value=f'`{cprefix}help other || разное || другое || остальное`')

    await ctx.send(embed=embed)

@help.command(aliases=['музыка'])
async def music(ctx):
    cprefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title='Справочник по музыке', color=0xff0800)
    embed.add_field(name=f'`{cprefix}play || музыка [ССЫЛКА]`', value='Запускает музыку из ютюба', inline=False)
    embed.add_field(name=f'`{cprefix}stop || стоп`', value='Останавливает музыку', inline=False)
    embed.add_field(name=f'`{cprefix}pause || пауза`', value='Ставит музыку на паузу [НЕ РАБОТАЕТ]', inline=False)
    embed.add_field(name=f'`{cprefix}resume`', value='Возобновляет музыку [НЕ РАБОТАЕТ]', inline=False)

    await ctx.send(embed=embed)



@help.command(aliases=['модерация'])
async def moderation(ctx):
    cprefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title='Справочник по модерации', color=0xff0800)
    embed.add_field(name=f'`{cprefix}mute || мут [НИК] [ВРЕМЯ(секунды)] [ПРИЧИНА]`', value='Мутит участника голосового канала', inline=False)
    embed.add_field(name=f'`{cprefix}unmute || анмут [НИК]`', value='Снимает мут', inline=False)
    embed.add_field(name=f'`{cprefix}ban || бан [НИК] [ПРИЧИНА]`', value='Банит участника', inline=False)
    embed.add_field(name=f'`{cprefix}unban [НИК]`', value='Снимает бан', inline=False)
    embed.add_field(name=f'`{cprefix}kick || кик [НИК]`', value='Кикает участника', inline=False)
    embed.add_field(name=f'`{cprefix}clear || очистить [КОЛИЧЕСТВО]`', value='Удаляет определённое количество сообщение в канале', inline=False)
    embed.add_field(name=f'`{cprefix}nick || ник [СТАРЫЙ] [НОВЫЙ]`', value='Меняет ник у участника')

    await ctx.send(embed=embed)


@help.command(aliases=['разное', 'другое', 'остальное'])
async def other(ctx):
    cprefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title='Справочник по остальным командам', color=0xff0800)
    embed.add_field(name=f'`{cprefix}random || рандом [ОТ] [ДО]`', value='Выдаёт рандомное число в заданном промежутке', inline=False)
    embed.add_field(name=f'`{cprefix}exercise || реши [ПРИМЕР]`', value='Решает простой математический пример', inline=False)
    embed.add_field(name=f'`{cprefix}info || инфо [НИК]`', value='Выдаёт информацию о пользователе', inline=False)

    await ctx.send(embed=embed)



# EVENTS
@bot.event
async def on_ready():
    print('Бот {0.user} готов к работе!'.format(bot))
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='PornHub Premium', type=discord.ActivityType.watching))


@bot.event
async def on_member_join(member):
    print(f'{member} Join')


@bot.event
async def on_member_remove(member):
    print(f'{member} Disconnected')


@bot.event
async def on_guild_join(guild): # Когда бот подключается к серверу, записывается в json айди сервера и префикс для команд
    with open('jsons/prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(guild.id)] = '.'

    with open('jsons/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@bot.event
async def on_guild_remove(guild): # Когда бот отключается от сервера, удалятеся информация о префиксе
    with open('jsons/prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes.pop(str(guild.id))

    with open('jsons/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

# COMMANDS

@bot.command(name='load', help='Загрузка отдельных модулей', hidden=True)
async def load(ctx, extension):
    bot.load_extension(f'extensions.{extension}')
    embed = discord.Embed(title=f'Плагин {extension} загружен!')
    await ctx.send(embed=embed)

@bot.command(name='unload', help='Выгрузка отдельных модулей', hidden=True)
async def unload(ctx, extension):
    bot.unload_extension(f'extensions.{extension}')
for filename in os.listdir('./extensions'):
    if filename.endswith('.py'):
        bot.load_extension(f'extensions.{filename[:-3]}')

@bot.command(aliases=['реши'], help='Решает простой математический пример')
async def exercise(ctx, arg): # Решает простой матемаический пример
    exercise = arg
    try:
        exercise = eval(exercise)
        await ctx.send(exercise)
    except Exception:
        await ctx.send('Указаны неверные числа/действие!!!')
    

@bot.command(aliases=['рандом'],name='random', help='Выдаёт рандомное число в заданном промежутке')
async def random_num(ctx, arg1, arg2): # Выдаёт рандомное число в заданном промежутке
    arg1 = int(arg1)
    arg2 = int(arg2)
    num = random.randint(arg1,arg2)
    await ctx.reply(f'Рандомное число: {num}')


@bot.command(aliases=['инфо'], help='Выводит информацию об участнике канала')
async def info(ctx, *, member: discord.Member): # Выводит информацию об участнике канала
    embed = discord.Embed(title='Информация о пользователе:', color = 0xff0000)
    embed.add_field(name='Имя:', value=member, inline=False)
    embed.add_field(name='Дата присоединения:', value=member.joined_at.strftime("%#d %B %Y"), inline=False)
    embed.add_field(name='Дата регистрации:', value=member.created_at.strftime("%#d %B %Y"), inline=False)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name='Роли:', value=member.roles)

    await ctx.send(embed=embed)


@bot.command(aliases=['роль+'], help='Выдаёт роль участнику')
async def add_role(ctx, member: discord.Member, role: discord.Role): # Выдаёт роль участнику
    if ctx.author.guild_permissions.administrator:
        await member.add_roles(role)
        embed = discord.Embed(title=f'{member} теперь {role}',color = 0x00ff00)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms1(ctx)
    

@bot.command(aliases=['роль-'], help='Удаляёт роль у участника')
async def remove_role(ctx, member: discord.Member, role: discord.Role): # Убирает роль с участника
    if ctx.author.guild_permissions.administrator:
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = 0x00ff00) 
        await ctx.send(embed=embed)
    else:
        await not_enough_perms1(ctx)


@bot.command(aliases=['префикс'], help='Меняет префикс у команд')
async def changeprefix(ctx, prefix): # Меняет префикс у команд
    if ctx.author.guild_permissions.administrator:
        with open('jsons/prefixes.json', 'r') as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open('jsons/prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

        embed = discord.Embed(title=f'Префикс команд поменялся на {prefix}')
        await ctx.send(embed=embed)
    else:
        await not_enough_perms1(ctx)


@bot.command(aliases=['ник'], help='Меняет ник у участника')
async def nick(ctx, member:discord.Member, newnick):
    oldnick = member
    await member.edit(nick=newnick)
    await ctx.send(f'{oldnick.mention} стал {newnick}')

@bot.command(aliases=['очистить'], help='Удаляет определённое количество сообщений в текстовом канале')
async def clear(ctx, amount:int):
    await ctx.channel.purge(limit=amount+1)
    

# ERRORS
@info.error
@add_role.error
@remove_role.error
async def info_error(ctx, error): # Выдаёт сообщение, если пользователь не найден
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title='Пользователь не найден!', color=0xff0000)
        await ctx.send(embed=embed)




@bot.command(hidden=True)
async def not_enough_perms1(ctx):
    embed = discord.Embed(title=f'У вас недостаточно прав!',color = 0x00ff00)
    await ctx.send(embed=embed)

@nick.error
async def nick_error(ctx, error):
    await ctx.send(error)
bot.run(TOKEN)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title='Неверно указано количество сообщений!', color=0xff0000)
        await ctx.send(embed=embed)