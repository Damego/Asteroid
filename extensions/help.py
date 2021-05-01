import discord
from discord.ext import commands
import json

def get_prefixs(message): 
    """Get guild prexif from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)

    return server[str(message.guild.id)]['prefix']

def get_embed_color(message):
    """Get color for embeds from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)

    return int(server[str(message.guild.id)]['embed_color'], 16)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.group(invoke_without_command=True) 
    async def help(self, ctx):
        cprefix = get_prefixs(ctx.message)
        embed = discord.Embed(title='Справочник команд', color=get_embed_color(ctx.message)) 
        embed.add_field(name='Музыка', value=f'`{cprefix}help music || музыка`', inline=False)
        embed.add_field(name='Модерация', value=f'`{cprefix}help moderation || модерация`', inline=False)
        embed.add_field(name='Разное', value=f'`{cprefix}help other || разное || другое || остальное`')

        if ctx.message.author.has_guild_permissions(administrator=True):
            embed.add_field(name='Администрация', value=f'`{cprefix}help admin || админ || администрация`')

        await ctx.send(embed=embed)

    @help.command(aliases=['музыка'])
    async def music(self, ctx):
        cprefix = get_prefixs(ctx.message)
        embed = discord.Embed(title='Справочник по музыке', color=get_embed_color(ctx.message))
        embed.add_field(name=f'`{cprefix}play || музыка [ССЫЛКА]`', value='Запускает музыку из ютюба', inline=False)
        embed.add_field(name=f'`{cprefix}stop || стоп`', value='Останавливает музыку', inline=False)
        embed.add_field(name=f'`{cprefix}pause || пауза`', value='Ставит музыку на паузу', inline=False)
        embed.add_field(name=f'`{cprefix}resume`', value='Возобновляет музыку', inline=False)

        await ctx.send(embed=embed)

    @help.command(aliases=['модерация'])
    async def moderation(self, ctx):
        cprefix = get_prefixs(ctx.message)
        embed = discord.Embed(title='Справочник по модерации', color=get_embed_color(ctx.message))
        embed.add_field(name=f'`{cprefix}mute || мут [НИК] [ВРЕМЯ(секунды)] [ПРИЧИНА]`', value='Мутит участника голосового канала', inline=False)
        embed.add_field(name=f'`{cprefix}unmute || анмут [НИК]`', value='Снимает мут', inline=False)
        embed.add_field(name=f'`{cprefix}ban || бан [НИК] [ПРИЧИНА]`', value='Банит участника', inline=False)
        embed.add_field(name=f'`{cprefix}unban [НИК]`', value='Снимает бан', inline=False)
        embed.add_field(name=f'`{cprefix}kick || кик [НИК]`', value='Кикает участника', inline=False)
        embed.add_field(name=f'`{cprefix}clear || очистить [КОЛИЧЕСТВО]`', value='Удаляет сообщения в канале', inline=False)
        embed.add_field(name=f'`{cprefix}nick || ник [СТАРЫЙ] [НОВЫЙ]`', value='Меняет ник у участника')

        await ctx.send(embed=embed)

    @help.command(aliases=['разное', 'другое', 'остальное'])
    async def other(self, ctx):
        cprefix = get_prefixs(ctx.message)
        embed = discord.Embed(title='Справочник по остальным командам', color=get_embed_color(ctx.message))
        embed.add_field(name=f'`{cprefix}random || рандом [ОТ] [ДО]`', value='Выдаёт рандомное число в заданном промежутке', inline=False)
        embed.add_field(name=f'`{cprefix}exercise || реши [ПРИМЕР]`', value='Решает простой математический пример', inline=False)
        embed.add_field(name=f'`{cprefix}info || инфо [НИК]`', value='Выдаёт информацию о пользователе', inline=False)
        embed.add_field(name=f'`{cprefix}QR || код [ТЕКСТ]`', value='Создаёт QR-код')

        await ctx.send(embed=embed)
    
    @help.command(aliases=['admin', 'админ', 'администрация'])
    @commands.has_guild_permissions(administrator=True)
    async def administration(self, ctx):
        cprefix = get_prefixs(ctx.message)
        embed = discord.Embed(title='Справочник по Администрации', color=get_embed_color(ctx.message))
        embed.add_field(name=f'`{cprefix}add_xp || опыт [НИК] [КОЛИЧЕСТВО]`', value='Выдаёт опыт', inline=False)
        embed.add_field(name=f'`{cprefix}changeprefix || префикс [ПРЕФИКС]`', value='Задаёт новый префикс команд', inline=False)
        embed.add_field(name=f'`{cprefix}change_embed_color || цвет [ЦВЕТ]`', value='Задаёт новый цвет', inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))