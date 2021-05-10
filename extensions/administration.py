import discord
from discord.ext import commands
import json
import os
from replit import Database, db

if db != None:
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

        
    @commands.command(description='Устанавливает опыт участнику')
    @commands.has_guild_permissions(administrator=True)
    async def set_xp(self, message, member:discord.Member, xp:int):
        server[str(message.guild.id)]['users'][str(member.id)]['xp'] = xp
        exp = server[str(message.guild.id)]['users'][str(member.id)]['xp']
        level_end = exp ** (1/4)

        server[str(message.guild.id)]['users'][str(member.id)]['level'] = round(level_end)
        lvl = server[str(message.guild.id)]['users'][str(member.id)]['level']
        await message.channel.send(f'{member.mention} получил {lvl}-й уровень')


    @commands.command(description='Устанавливает уровень участнику')
    @commands.has_guild_permissions(administrator=True)
    async def set_lvl(self, message, member:discord.Member, lvl:int):
        server[str(message.guild.id)]['users'][str(member.id)]['level'] = lvl
        await message.channel.send(f'{member.mention} получил {lvl}-й уровень')


def setup(bot):
    bot.add_cog(Administration(bot))