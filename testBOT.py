import random
import json
import discord
from discord.ext import commands

TOKEN = 'ODI4MjYyMjc1MjA2ODczMTA4.YGnBWg.u0AhcolLPnXPe5CZxTx0k9XTqts'
userhelp = open('help.txt', encoding='UTF-8')

def get_prefix(bot, message): 
    with open('jsons/prefixes.json', 'r') as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]

bot = commands.Bot(command_prefix=get_prefix)



# EVENTS
@bot.event
async def on_ready():
  print('Бот {0.user} готов к работе!'.format(bot))


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

@bot.command(aliases=['реши'])
async def exercise(ctx, arg): # Решает простой матемаический пример
    exercise = arg
    try:
        exercise = eval(exercise)
        await ctx.send(exercise)
    except Exception:
        await ctx.send('Указаны неверные числа/действие!!!')
    

@bot.command(aliases=['рандом'])
async def random_num(ctx, arg1, arg2): # Выдаёт рандомное число в заданном промежутке
    arg1 = int(arg1)
    arg2 = int(arg2)
    num = random.randint(arg1,arg2)
    await ctx.reply(f'Рандомное число: {num}')


@bot.command(aliases=['помощь'])
async def user_help(ctx):
    await ctx.send(userhelp.read())


@bot.command(aliases=['инфо'])
async def info(ctx, *, member: discord.Member): # Выводит информацию об участнике канала
    embed = discord.Embed(title='Информация о пользователе:', color = 0xff0000)
    embed.add_field(name='Имя:', value=member, inline=False)
    embed.add_field(name='Дата присоединения:', value=member.joined_at.strftime("%#d %B %Y"), inline=False)
    embed.add_field(name='Дата регистрации:', value=member.created_at.strftime("%#d %B %Y"), inline=False)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name='Роли:', value=ctx.guild.get_role)

    await ctx.send(embed=embed)


@bot.command(aliases=['роль+'])
async def add_role(ctx, member: discord.Member, role: discord.Role): # Выдаёт роль участнику
    if ctx.author.guild_permissions.administrator:
        await member.add_roles(role)
        embed = discord.Embed(title=f'{member} теперь {role}',color = 0x00ff00)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms(ctx)
    

@bot.command(aliases=['роль-'])
async def remove_role(ctx, member: discord.Member, role: discord.Role): # Убирает роль с участника
    if ctx.author.guild_permissions.administrator:
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = 0x00ff00) 
        await ctx.send(embed=embed)
    else:
        await not_enough_perms(ctx)


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
        await not_enough_perms(ctx)


@bot.command(aliases=['мут'])
async def mute(ctx, member:discord.Member, * ,reason=None):
    if ctx.author.guild_permissions.administrator:
        await member.edit(mute=True)
        embed = discord.Embed(title=f'{member} был отправлен в мут!',description=f'Причина: {reason}', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms(ctx)

@bot.command(aliases=['дизмут', 'анмут'])
async def unmute(ctx, member:discord.Member):
    if ctx.author.guild_permissions.administrator:
        await member.edit(mute=False)
        embed = discord.Embed(title=f'Мут с {member} снят!', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms(ctx)

@bot.command(aliases=['бан'])
async def ban(ctx, member:discord.Member, *, reason=None):
    if ctx.author.guild_permissions.administrator:
        await member.ban(reason=reason)
        embed = discord.Embed(title=f'{member} был заблокирован!',description=f'Причина: {reason}', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms(ctx)


@bot.command(aliases=['анбан', 'дизбан'])
async def unban(ctx, member):
    if ctx.author.guild_permissions.administrator:
        banned_users = await ctx.guild.bans()
        member_name, member_disc = member.split('#')

        for ban in banned_users:
            user = ban.user
            if (user.name, user.discriminator) == (member_name, member_disc):
                await ctx.guild.unban(user)
                embed = discord.Embed(title=f'С пользователя {member} снята блокировка!', color=0xff0000)
                await ctx.send(embed=embed)
                return
    else:
        await not_enough_perms(ctx)

@bot.command(aliases=['кик'])
async def kick(ctx, member:discord.Member, *, reason=None):
    if ctx.author.guild_permissions.administrator:
        await member.kick(reason=reason)
        embed = discord.Embed(title=f'{member} был кикнут с сервера!',description=f'Причина: {reason}', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await not_enough_perms(ctx)

# ERRORS
@info.error
@add_role.error
@remove_role.error
async def info_error(ctx, error): # Выдаёт сообщение, если пользователь не найден
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title='Пользователь не найден!', color=0xff0000)
        await ctx.send(embed=embed)


@mute.error
@unmute.error
async def mute_error(ctx, error):
    embed = discord.Embed(title='Пользователь не подключен к голосовому каналу!', color=0xff0000)
    await ctx.send(embed=embed)

@bot.command()
async def not_enough_perms(ctx):
    embed = discord.Embed(title=f'У вас недостаточно прав!',color = 0x00ff00)
    await ctx.send(embed=embed)


bot.run(TOKEN)
