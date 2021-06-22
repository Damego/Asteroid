import os
from random import randint, choice

import discord
from discord.ext import commands
import qrcode
from discord_components import DiscordComponents, Button, ButtonStyle


from extensions.bot_settings import get_embed_color, get_db
server = get_db()

def get_stats(message, member):
    """Get guild members stats from json """
    ls = {
        'xp':server[str(message.guild.id)]['users'][str(member.id)]['xp'],
        'lvl':server[str(message.guild.id)]['users'][str(member.id)]['level']
        }
    return ls

def get_emoji_status(message):
    """Get guild emoji status for stats from json """
    ls = {
        'online':server[str(message.guild.id)]['emoji_status']['online'],
        'dnd':server[str(message.guild.id)]['emoji_status']['dnd'],
        'idle':server[str(message.guild.id)]['emoji_status']['idle'],
        'offline':server[str(message.guild.id)]['emoji_status']['offline'],
        }
    return ls

class Misc(commands.Cog, description='Остальное'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.command(aliases=['рандом'], name='random', description='Выдаёт рандомное число в заданном промежутке', help='[от] [до]')
    async def random_num(self, ctx, arg1:int, arg2:int):
        num = randint(arg1,arg2)
        await ctx.reply(f'Рандомное число: {num}')

    @commands.command(name='coin', aliases=['орел', 'решка','монетка'], description='Кидает монетку, может выпасть орёл или решка', help=' ')
    async def coinflip(self, ctx):
        ls = ['Орёл', 'Решка']
        result = choice(ls)
        if result == 'Орёл':
            result = 'Вам выпал Орёл! <:eagle_coin:855061929827106818>'
        else:
            result = 'Вам выпала Решка! <:tail_coin:855060316609970216>'
        await ctx.reply(result)


    @commands.command(aliases=['инфо'], description='Выводит информацию об участнике канала', help='[ник]')
    async def info(self, ctx, *, member: discord.Member):
        embed = discord.Embed(title=f'Информация о пользователе {member}', color=get_embed_color(ctx.message))

        member_roles = []
        for role in member.roles:
            if role.name != "@everyone":
                member_roles.append(role.mention)
        member_roles = member_roles[::-1]
        member_roles = ', '.join(member_roles)
        

        member_status = str(member.status)
        status = {
            'online':'<:s_online:850792217031082051> В сети',
            'dnd':'<:dnd:850792216943525936> Не беспокоить',
            'idle':'<:s_afk:850792216732368937> Не активен',
            'offline':'<:s_offline:850792217262030969> Не в сети'
        }

        embed.add_field(name= "Основная информация:", value=f"""
            **Дата регистрации в Discord:** {member.created_at.strftime("%#d %B %Y")}
            **Дата присоединения на сервер:** {member.joined_at.strftime("%#d %B %Y")}
            **Текущий статус:** {status.get(member_status)}
            **Роли:** {member_roles}
            """, inline=False)

        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(name='qr', aliases=['QR', 'код'], description='Создаёт QR-код', help='[текст]')
    async def create_qr(self, ctx, *, text):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1
        )
        qr.add_data(data=text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f'./qrcodes/{ctx.message.author.id}.png')
        await ctx.send(file = discord.File(f'./qrcodes/{ctx.message.author.id}.png'))
        os.remove(f'./qrcodes/{ctx.message.author.id}.png')

    @commands.command(description='Показывает пинг бота', help='')
    async def ping(self, ctx):
        embed = discord.Embed()
        embed.add_field(name='🏓 Pong!', value=f'Задержка бота `{int(ctx.bot.latency * 1000)}` мс')
        await ctx.send(embed=embed)



def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Misc(bot))
