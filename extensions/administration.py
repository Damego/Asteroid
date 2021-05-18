import os

import discord
from discord.ext import commands
from replit import Database, db

if not db:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)


class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(aliases=['префикс'], description='Меняет префикс у команд')
    async def changeprefix(self, ctx, prefix):
        server[str(ctx.guild.id)]['prefix'] = prefix

        embed = discord.Embed(title=f'Префикс команд поменялся на {prefix}')
        await ctx.send(embed=embed)

    @commands.command(aliases=['e_color', 'цвет'], description='Меняет цвет у сообщений бота')
    @commands.has_guild_permissions(administrator=True)
    async def change_embed_color(self, ctx, new_color):
        server[str(ctx.guild.id)]['embed_color'] = '0x'+new_color


def setup(bot):
    bot.add_cog(Administration(bot))