import discord
from discord.ext import commands
import json

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
        with open('jsons/servers.json', 'r') as f:
            server = json.load(f)

        server[str(guild.id)] = {
            'prefix':'.',
            'embed_color': 0xFFFFFE,
            'emoji_status': {},
            'users': {}
        }

        with open('jsons/servers.json', 'w') as f:
            json.dump(server, f, indent=4)


    @commands.Cog.listener()
    async def on_guild_remove(self, guild): # Когда бот отключается от сервера, удалятеся информация о сервере
        with open('jsons/servers.json', 'r') as f:
            server = json.load(f)

        server.pop(str(guild.id))

        with open('jsons/servers.json', 'w') as f:
            json.dump(server, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user = message.author.id
            with open('jsons/servers.json', 'r') as f:
                server = json.load(f)

            if not str(user) in server[str(message.guild.id)]['users']:
                await self.add_member(server, message)
            else:
                await self.update_member(server, message, 5)

            with open('jsons/servers.json', 'w') as f:
                json.dump(server, f, indent=4)


    async def add_member(self, server, message):
        server[str(message.guild.id)]['users'][str(message.author.id)] = {}
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

    @commands.command(aliases=['опыт'])
    @commands.has_guild_permissions(administrator=True)
    async def add_xp(self, message, member:discord.Member, xp:int):
        with open('jsons/servers.json', 'r') as f:
            server = json.load(f)

        server[str(message.guild.id)]['users'][str(member.id)]['xp'] += xp

        with open('jsons/servers.json', 'w') as f:
            json.dump(server, f, indent=4)



def setup(bot):
    bot.add_cog(Level(bot))