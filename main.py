import discord
from discord import utils, ext
from discord.ext import commands

import config

class MyBot(discord.Client):
    async def on_ready(self):
        print('{0} включился!'.format(self.user))

    async def on_connect(self):
        print('{0} подключился!'.format(self.user))

    

    
botx = MyBot()
bot = commands.Bot(command_prefix='!')

@bot.command()
async def reply(ctx, arg):
    await ctx.send(arg)

botx.run(config.TOKEN)
