import os
from random import randint

import discord
from discord.ext import commands
from replit import Database, db

if db != None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.add_member(server, member)
        print(f'{member} Join')


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} Disconnected')


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user = message.author.id

            if not str(message.guild.id) in server:
                await self.add_guild_in_json(message.guild)

            if not str(user) in server[str(message.guild.id)]['users']:
                await self.add_member(server, message)
            else:
                xp = randint(5,10)
                await self.update_member(server, message, xp)



    async def add_member(self, server, message):
        server[str(message.guild.id)]['users'][str(message.author.id)] = {}
        server[str(message.guild.id)]['users'][str(message.author.id)]['role'] = ""
        server[str(message.guild.id)]['users'][str(message.author.id)]['xp'] = 0
        server[str(message.guild.id)]['users'][str(message.author.id)]['level'] = 1

    async def update_member(self, server, message, xp):
        server[str(message.guild.id)]['users'][str(message.author.id)]['xp'] += xp
        exp = server[str(message.guild.id)]['users'][str(message.author.id)]['xp']
        level_start = server[str(message.guild.id)]['users'][str(message.author.id)]['level']
        level_end = exp ** (1/4)

        if level_start < level_end:
            server[str(message.guild.id)]['users'][str(message.author.id)]['level'] += 1
            lvl = server[str(message.guild.id)]['users'][str(message.author.id)]['level']
            await message.channel.send(f'{message.author.mention} получил {lvl}-й уровень')

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
    bot.add_cog(Level(bot))