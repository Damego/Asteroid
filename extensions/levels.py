import os
from random import randint

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

class Levels(commands.Cog, description='Cистема уровней'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.add_member(server, member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user = message.author.id

            if not str(user) in server[str(message.guild.id)]['users']:
                await self.add_member(server, message)
            else:
                xp = randint(5,10)
                await self.update_member(server, message, xp)

    async def add_member(self, server, message):
        userstats = server[str(message.guild.id)]['users'][str(message.author.id)]
        userstats = {}
        userstats['role'] = ""
        userstats['xp'] = 0
        userstats['level'] = 1

    async def update_member(self, server, message, xp):
        userstats = server[str(message.guild.id)]['users'][str(message.author.id)]
        userstats['xp'] += xp
        exp = userstats['xp']
        level_start = userstats['level']
        level_end = exp ** (1/4)

        if level_start < level_end:
            userstats['level'] += 1
            lvl = userstats['level']
            await message.channel.send(f'{message.author.mention} получил {lvl}-й уровень')

    @commands.command(description='Устанавливает опыт участнику', help='[ник] [опыт]')
    @commands.has_guild_permissions(administrator=True)
    async def set_xp(self, message, member:discord.Member, xp:int):
        userstats = server[str(message.guild.id)]['users'][str(member.id)]
        
        userstats['xp'] = xp
        exp = userstats['xp']
        level_end = exp ** (1/4)

        userstats['level'] = round(level_end)
        lvl = userstats['level']
        await message.channel.send(f'{member.mention} получил {lvl}-й уровень')

    @commands.command(description='Устанавливает уровень участнику', help='[ник] [уровень]')
    @commands.has_guild_permissions(administrator=True)
    async def set_lvl(self, message, member:discord.Member, lvl:int):
        userstats = server[str(message.guild.id)]['users'][str(member.id)]
        
        userstats['level'] = lvl
        userstats['xp'] = lvl ** 4

        await message.channel.send(f'{member.mention} получил {lvl}-й уровень')


def setup(bot):
    bot.add_cog(Levels(bot))