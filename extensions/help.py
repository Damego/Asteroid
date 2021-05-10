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

def get_prefixs(message): 
    """Get guild prexif from json """
    return server[str(message.guild.id)]['prefix']

def get_embed_color(message):
    """Get color for embeds from json """
    return int(server[str(message.guild.id)]['embed_color'], 16)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')


    @commands.group(invoke_without_command=True,description='Показывает это сообщение')
    async def help(self, ctx):
        cprefix = get_prefixs(ctx.message)
        embed = discord.Embed(title='Справочник команд', color=get_embed_color(ctx.message)) 
        embed.add_field(name='Музыка', value=f'`{cprefix}help Music`', inline=False)
        embed.add_field(name='Модерация', value=f'`{cprefix}help Moderation`', inline=False)
        embed.add_field(name='Разное', value=f'`{cprefix}help Other`', inline=False)
        if ctx.message.author.guild_permissions.administrator:
            embed.add_field(name='Администрация', value=f'`{cprefix}help Administration`', inline=False)

            await ctx.send(embed=embed)


    @help.command(aliases=['Music','музыка','music'], description='Показывает команды Музыки')
    async def music_cmds(self, ctx):
        cprefix = get_prefixs(ctx.message)
        name = 'Music'
        embed = None
        for commands.command in self.bot.commands:
            if commands.command.cog_name == name:
                if embed is None:
                    embed = discord.Embed(title=f'Справочник по {commands.command.cog_name}', color=get_embed_color(ctx.message))
                embed.add_field(name=f'`{cprefix}{commands.command}`', value=f'{commands.command.description}', inline=False)
        await ctx.send(embed=embed)

    @help.command(aliases=['moder','Moder','модер','Moderation'], description='Показывает команды Модерации')
    async def moderation_cmds(self, ctx):
        cprefix = get_prefixs(ctx.message)
        name = 'Moderation'
        embed = None
        for commands.command in self.bot.commands:
            if commands.command.cog_name == name:
                if embed is None:
                    embed = discord.Embed(title=f'Справочник по {commands.command.cog_name}', color=get_embed_color(ctx.message))
                embed.add_field(name=f'`{cprefix}{commands.command}`', value=f'{commands.command.description}', inline=False)
        await ctx.send(embed=embed)

    @help.command(aliases=['Admin','admin','админ','Админ','Administration'], description='Показывает команды Администрации')
    async def administration_cmds(self, ctx):
        cprefix = get_prefixs(ctx.message)
        name = 'Administration'
        embed = None
        for commands.command in self.bot.commands:
            if commands.command.cog_name == name:
                if embed is None:
                    embed = discord.Embed(title=f'Справочник по {commands.command.cog_name}', color=get_embed_color(ctx.message))
                embed.add_field(name=f'`{cprefix}{commands.command}`', value=f'{commands.command.description}', inline=False)
        await ctx.send(embed=embed)

    @help.command(aliases=['Other','other','другое','остальное',], description='Показывает остальные команды')
    async def other_cmds(self, ctx):
        cprefix = get_prefixs(ctx.message)
        name = 'Other'
        embed = None
        for commands.command in self.bot.commands:
            if commands.command.cog_name == name:
                if embed is None:
                    embed = discord.Embed(title=f'Справочник по {commands.command.cog_name}', color=get_embed_color(ctx.message))
                embed.add_field(name=f'`{cprefix}{commands.command}`', value=f'{commands.command.description}', inline=False)
        await ctx.send(embed=embed)







def setup(bot):
    bot.add_cog(Help(bot))