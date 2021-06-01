import os

import discord
from discord.ext import commands
from replit import Database, db

if db is not None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)


class Administration(commands.Cog, description='Администрация'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name='prefix', aliases=['префикс'], description='Меняет префикс для команд', help='[префикс]')
    async def change_guild_prefix(self, ctx, prefix):
        server[str(ctx.guild.id)]['prefix'] = prefix

        embed = discord.Embed(title=f'Префикс для команд изменился на `{prefix}`')
        await ctx.send(embed=embed)

    @commands.command(name='color', aliases=['цвет'], description='Меняет цвет сообщений бота', help='[цвет(HEX)]')
    @commands.has_guild_permissions(administrator=True)
    async def change_guild_embed_color(self, ctx, new_color):
        server[str(ctx.guild.id)]['embed_color'] = '0x'+new_color


def setup(bot):
    bot.add_cog(Administration(bot))