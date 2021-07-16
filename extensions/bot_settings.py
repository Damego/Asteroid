from os import getenv

import discord
from discord.ext import commands

def get_db():
    from replit import Database, db
    if db is not None:
        return db
    from dotenv import load_dotenv
    load_dotenv()
    url = getenv('URL')
    return Database(url)

def get_embed_color(guild_id):
    """Get color for embeds from json """
    return int(server[str(guild_id)]['configuration']['embed_color'], 16)

def get_prefix(guild_id):
    """Get guild prexif from json """
    return server[str(guild_id)]['configuration']['prefix']


version = 'v1.0.2'

server = get_db()

multiplier = {
    'д': 86400,
    'ч': 3600,
    'м': 60,
    'с': 1,
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1
    }


def is_bot_or_guild_owner():
    async def predicate(ctx):
        return ctx.author.id in [ctx.bot.owner_id, ctx.guild.owner_id]
    return commands.check(predicate)



class DurationConverter(commands.Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        time_format = argument[-1]

        if amount.isdigit() and time_format in ['д', 'ч', 'м', 'с', 'd', 'h', 'm', 's']:
            return (int(amount), time_format)

        raise commands.BadArgument(message='Неверный формат времени!')



class Settings(commands.Cog, description='Настройка бота'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        

    @commands.has_guild_permissions(administrator=True)
    @commands.group(
        invoke_without_command=True,
        name='set',
        description='Команда, позволяющая изменять настройки бота',
        help='[команда]',
        usage='Только для Администрации')
    async def set_conf(self, ctx:commands.Context):
        await ctx.send('Используйте команды: `set prefix` или `set color`', delete_after=10)

    
    @set_conf.command(
        name='prefix',
        aliases=['префикс'],
        description='Меняет префикс для команд',
        help='[префикс]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def change_guild_prefix(self, ctx:commands.Context, prefix):
        server[str(ctx.guild.id)]['configuration']['prefix'] = prefix

        embed = discord.Embed(title=f'Префикс для команд изменился на `{prefix}`', color=0x2f3136)
        await ctx.send(embed=embed, delete_after=30)

    @set_conf.command(
        name='color',
        aliases=['цвет'],
        description='Меняет цвет сообщений бота',
        help='[цвет(HEX)]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def change_guild_embed_color(self, ctx:commands.Context, color:str):
        if color.startswith('#') and len(color) == 7:
            color = color.replace('#', '')
        elif len(color) != 6:
            await ctx.send('Неверный формат цвета')
            return
            
        newcolor = '0x' + color
        server[str(ctx.guild.id)]['configuration']['embed_color'] = newcolor

        embed = discord.Embed(title=f'Цвет сообщений был изменён!', color=int(newcolor, 16))
        await ctx.send(embed=embed)

    @commands.command(name='prefix', description='Показывает текущий префикс на сервере', help=' ')
    async def show_guild_prefix(self, ctx:commands.Context):
        embed = discord.Embed(title=f'Текущий префикс: `{get_prefix(ctx.guild.id)}`', color=0x2f3136)
        await ctx.send(embed=embed)

    @commands.command(aliases=['cl'], name='changelog', description='Показывает изменения последнего обновления', help='')
    async def changelog(self, ctx:commands.Context):
        with open('changelog.txt', 'r', encoding='UTF-8') as file:
            version = file.readline()
            text = file.read()

        embed = discord.Embed(title=version, description=text, color=0x2f3136)
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Settings(bot))