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

def get_embed_color(message):
    """Get color for embeds from json """
    return int(server[str(message.guild.id)]['configuration']['embed_color'], 16)

def get_prefix(message):
    """Get guild prexif from json """
    prefix = server[str(message.guild.id)]['configuration']['prefix']
    return prefix

server = get_db()


class Settings(commands.Cog, description='Настройка бота'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.has_guild_permissions(administrator=True)
    @commands.group(invoke_without_command=True, name='set', description='Команда, позволяющая изменять настройки бота', help='[арг]')
    async def set_conf(self, ctx):
        await ctx.send('Используйте команды: `set prefix` или `set color`', delete_after=10)

    
    @set_conf.command(name='prefix', aliases=['префикс'], description='Меняет префикс для команд', help='[префикс]')
    async def change_guild_prefix(self, ctx, prefix):
        server[str(ctx.guild.id)]['configuration']['prefix'] = prefix

        embed = discord.Embed(title=f'Префикс для команд изменился на `{prefix}`', color=0x2f3136)
        await ctx.send(embed=embed, delete_after=10)

    @set_conf.command(name='color', aliases=['цвет'], description='Меняет цвет сообщений бота', help='[цвет(HEX)]')
    async def change_guild_embed_color(self, ctx, color):
        newcolor = '0x'+color
        server[str(ctx.guild.id)]['configuration']['embed_color'] = newcolor

        embed = discord.Embed(title=f'Изменился цвет сообщений бота !`', color=int(newcolor, 16))
        await ctx.send(embed=embed, delete_after=10)

    @commands.command(name='prefix', description='Показывает текущий префикс на сервере', help=' ')
    async def show_guild_prefix(self, ctx):
        embed = discord.Embed(title=f'Текущий префикс: `{get_prefix(ctx.message)}`', color=0x2f3136)
        await ctx.send(embed=embed)




def setup(bot):
    bot.add_cog(Settings(bot))