import random
import json
import discord
from discord.ext import commands
import qrcode
import asyncio
import os


def get_prefix(bot, message): 
    with open('jsons/prefixes.json', 'r') as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]

def get_token(): 
    with open('jsons/config.json', 'r') as f:
        token = json.load(f)

    return token["TOKEN"]

def get_react_post_id():
    with open('jsons/config.json', 'r') as f:
        token = json.load(f)

    return token["REACTION_POST_ID"]

def get_emoji_role(emoji):
    with open('jsons/roles.json', 'r') as f:
        token = json.load(f)

    return token[f"{emoji}"]

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
    embed.add_field(name=f'`{cprefix}pause || пауза`', value='Ставит музыку на паузу', inline=False)
    embed.add_field(name=f'`{cprefix}resume`', value='Возобновляет музыку', inline=False)

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
    embed.add_field(name=f'`{cprefix}qr [ТЕКСТ]`', value='Создаёт QR-код')

    await ctx.send(embed=embed)



# EVENTS
@bot.event
async def on_ready():
    print('Бот {0.user} готов к работе!'.format(bot))
    #await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='PornHub Premium', type=discord.ActivityType.watching))
    await change_activity()

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
    if ctx.message.author.is_owner():
        bot.unload_extension(f'extensions.{extension}')
for filename in os.listdir('./extensions'):
    if filename.endswith('.py'):
        bot.load_extension(f'extensions.{filename[:-3]}')

@bot.command(aliases=['реши'])
async def exercise(ctx, arg): # Решает простой матемаический пример
    exercise = arg
    try:
        exercise = eval(exercise)
        await ctx.send(exercise)
    except Exception:
        await ctx.send('Указаны неверные числа/действие!!!')
    

@bot.command(aliases=['рандом'],name='random')
async def random_num(ctx, arg1, arg2): # Выдаёт рандомное число в заданном промежутке
    arg1 = int(arg1)
    arg2 = int(arg2)
    num = random.randint(arg1,arg2)
    await ctx.reply(f'Рандомное число: {num}')


@bot.command(aliases=['инфо'])
async def info(ctx, *, member: discord.Member): # Выводит информацию об участнике канала
    embed = discord.Embed(title='Информация о пользователе:', color = 0xff0000)
    embed.add_field(name='Имя:', value=member, inline=False)
    embed.add_field(name='Дата присоединения:', value=member.joined_at.strftime("%#d %B %Y"), inline=False)
    embed.add_field(name='Дата регистрации:', value=member.created_at.strftime("%#d %B %Y"), inline=False)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name='Роли:', value=member.roles)

    await ctx.send(embed=embed)


@bot.command(aliases=['роль+'])
async def add_role(ctx, member: discord.Member, role: discord.Role): # Выдаёт роль участнику
    if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_roles:
        print(type(role))
        await member.add_roles(role)
        embed = discord.Embed(title=f'{member} теперь {role}',color = 0x00ff00)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms1(ctx)
    

@bot.command(aliases=['роль-'])
async def remove_role(ctx, member: discord.Member, role: discord.Role): # Убирает роль с участника
    if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_roles:
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = 0x00ff00) 
        await ctx.send(embed=embed)
    else:
        await not_enough_perms1(ctx)


@bot.command(aliases=['префикс'])
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


@bot.command(aliases=['ник'])
async def nick(ctx, member:discord.Member, newnick):
    if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_nicknames:
        oldnick = member
        await member.edit(nick=newnick)
        await ctx.send(f'{oldnick.mention} стал {newnick}')
    else:
        await not_enough_perms1(ctx)

@bot.command(aliases=['очистить', 'очистка', 'чистить',"чист"])
async def clear(ctx, amount:int):
    await ctx.channel.purge(limit=amount+1)

@bot.command(name='qr')
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

@bot.command()
async def cr_channel(ctx, *, text=None):
    if text == None:
        await ctx.guild.create_text_channel(f'{ctx.message.author}')
    else:
        await ctx.guild.create_text_channel(f'{text}') 
    


@bot.command()
async def create_post(ctx):
    embed = discord.Embed(title='Выбери свою любимую игру', color=0xff0800)
    embed.add_field(name=f':csgo:', value='`CS:GO`', inline=False)
    embed.add_field(name=f':gtav:', value='`GTA V`', inline=False)
    embed.add_field(name=f':osu:', value='`Osu!`', inline=False)
    embed.add_field(name=f':minecraft:', value='`Minecraft`')

    await ctx.send(embed=embed)









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