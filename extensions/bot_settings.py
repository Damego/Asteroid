from os import getenv

import discord
from discord.ext import commands

def get_db():
    from replit import Database, db
    if db is not None:
        server = db
    else:
        from dotenv import load_dotenv
        load_dotenv()
        url = getenv('URL')
        server = Database(url)
    return server

def get_embed_color(guild):
    """Get color for embeds from json """
    return int(server[str(guild.id)]['configuration']['embed_color'], 16)

def get_prefix(guild):
    """Get guild prexif from json """
    prefix = server[str(guild.id)]['configuration']['prefix']
    return prefix

def get_footer_text() -> str:
    text = 'Damego Bot v1.0.0 Beta'
    return text

server = get_db()

multiplier = {
    'д': 8640,
    'ч': 360,
    'м': 60,
    'с': 1,
    'd': 8640,
    'h': 360,
    'm': 60,
    's': 1
    }

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
    @commands.group(invoke_without_command=True, name='set', description='Команда, позволяющая изменять настройки бота', help='[арг]')
    async def set_conf(self, ctx):
        await ctx.send('Используйте команды: `set prefix` или `set color`', delete_after=10)

    
    @set_conf.command(name='prefix', aliases=['префикс'], description='Меняет префикс для команд', help='[префикс]')
    @commands.has_guild_permissions(administrator=True)
    async def change_guild_prefix(self, ctx, prefix):
        server[str(ctx.guild.id)]['configuration']['prefix'] = prefix

        embed = discord.Embed(title=f'Префикс для команд изменился на `{prefix}`', color=0x2f3136)
        await ctx.send(embed=embed, delete_after=30)

    @set_conf.command(name='color', aliases=['цвет'], description='Меняет цвет сообщений бота', help='[цвет(HEX)]')
    @commands.has_guild_permissions(administrator=True)
    async def change_guild_embed_color(self, ctx, color:str):
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
    async def show_guild_prefix(self, ctx):
        embed = discord.Embed(title=f'Текущий префикс: `{get_prefix(ctx.message)}`', color=0x2f3136)
        await ctx.send(embed=embed)

    @commands.command(aliases=['cl'], name='changelog', description='Показывает изменения последнего обновления', help='')
    async def changelog(self, ctx):
        with open('changelog.txt', 'r', encoding='UTF-8') as file:
            version = file.readline()
            text = file.read()

        embed = discord.Embed(title=version, description=text, color=0x2f3136)
        await ctx.send(embed=embed)




def setup(bot):
    bot.add_cog(Settings(bot))