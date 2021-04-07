import random
import discord
from discord.ext import commands

TOKEN = 'ODI4MjYyMjc1MjA2ODczMTA4.YGnBWg.u0AhcolLPnXPe5CZxTx0k9XTqts'
userhelp = open('help.txt', encoding='UTF-8')

bot = commands.Bot(command_prefix='!')

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

# COMMANDS
@bot.command()
async def reply(ctx, arg): # Отвечает этим же сообщением
    await ctx.reply(arg)

@bot.command(aliases=['реши'])
async def exercise(ctx, arg): # Решает простой матемаический пример
    exercise = arg
    try:
        exercise = eval(exercise)
        await ctx.send(exercise)
    except Exception:
        await ctx.send('Указаны неверные числа/действие!!!')
    
@bot.command()
async def hello(ctx):
    author = ctx.message.author
    
    await ctx.reply(f'Приветствую тебя, {author}')

@bot.command(aliases=['рандом'])
async def random_num(ctx, arg1, arg2):
    arg1 = int(arg1)
    arg2 = int(arg2)
    num = random.randint(arg1,arg2)
    await ctx.reply(f'Рандомное число: {num}')

@bot.command(aliases=['помощь'])
async def user_help(ctx):
    await ctx.send(userhelp.read())

@bot.command()
async def get_avatar(ctx, member: discord.Member):
    userdata = member.roles
    await ctx.send(f'{userdata}')

@bot.command(aliases=['инфо'])
async def info(ctx, *, member: discord.Member):
    embed = discord.Embed(title='Информация о пользователе:', color = 0xff0000)
    embed.add_field(name='Имя:', value=member, inline=False)
    embed.add_field(name='Дата присоединения:', value=member.joined_at.strftime("%#d %B %Y"), inline=False)
    embed.add_field(name='Дата регистрации:', value=member.created_at.strftime("%#d %B %Y"), inline=False)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name='Роли:', value=member.roles)

    await ctx.send(embed=embed)

@bot.command(aliases=['роль+'])
async def add_role(ctx, member: discord.Member, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        await member.add_roles(role)
        embed = discord.Embed(title=f'{member} теперь {role}',color = 0x00ff00)
        await ctx.send(embed=embed)
    
@bot.command(aliases=['роль-'])
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = 0x00ff00) 
        await ctx.send(embed=embed)

@info.error
async def info_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('I could not find that member...')










bot.run(TOKEN)
