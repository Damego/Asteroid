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

def get_prefix(message):
    """Get guild prexif from json database"""
    return server[str(message.guild.id)]['prefix']

def get_embed_color(message):
    """Get color for embeds from json database"""
    return int(server[str(message.guild.id)]['embed_color'], 16)


class Help(commands.Cog, description='Помощь'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.hidden = True
        

    @commands.command(description='Показывает это сообщение')
    async def help(self, ctx, extension=None):
        cprefix = get_prefix(ctx.message)

        if extension is None:
            embed = discord.Embed(color=0x2f3136)
            embed.add_field(name='\u200b', value='```               「📝」КОМАНДЫ:               ```', inline=False)
            for cog in self.bot.cogs:
                if not self.bot.cogs[cog].hidden:
                    embed.add_field(name=self.bot.cogs[cog].description, value=f'`{cprefix}help {cog}`')

        elif extension in self.bot.cogs:
            cog_name = self.bot.cogs[extension].description
            embed = discord.Embed(color=0x2f3136)
            embed.add_field(name='**Справочник команд**', value=f'```               「📝」{cog_name}               ```', inline=False)
            all_cmds = self.bot.cogs[extension].get_commands()
            for cmd in all_cmds:
                embed.add_field(name=f'`{cprefix}{cmd} {cmd.help}`', value=f'{cmd.description}', inline=False)
        else:
            embed = discord.Embed(title=f'Плагин `{extension}` не найден!',color=0x2f3136)
        await ctx.message.channel.purge(limit=1)
        await ctx.send(embed=embed, delete_after=60)


def setup(bot):
    bot.add_cog(Help(bot))