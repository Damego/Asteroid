import discord
from discord.ext import commands
import json
import os
from random import randint
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
        print(f'{member} Join')


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} Disconnected')


    @commands.Cog.listener()
    async def on_guild_join(self, guild): # Когда бот подключается к серверу, записывается в json айди сервера и префикс для команд
        server[str(guild.id)] = {
            'prefix':'.',
            'embed_color': 0xFFFFFE,
            'emoji_status': {"online":" ",
                            "dnd":" ",
                            "idle":" ",
                            "offline":" "},
            'users': {},
            'role_by_level': {}
        }

    @commands.Cog.listener()
    async def on_guild_remove(self, guild): # Когда бот отключается от сервера, удалятеся информация о сервере
        server.pop(str(guild.id))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user = message.author.id

            if not str(message.guild.id) in server:
                await self.add_guild_in_json(message.guild)

            if not str(user) in server[str(message.guild.id)]['users']:
                await self.add_member(server, message)
            else:
                xp = randint(15,25)
                await self.update_member(server, message, xp)


    async def add_guild_in_json(self, guild):
        """Add guild in json"""

        server[str(guild.id)] = {
            'prefix':'.',
            "embed_color": "0xFFFFFE",
            'emoji_status': {"online":" ",
                            "dnd":" ",
                            "idle":" ",
                            "offline":" "},
            'users': {},
            'role_by_level': {}
        }


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

        




def setup(bot):
    bot.add_cog(Level(bot))