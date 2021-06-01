import os
from random import randint

import discord
from discord.ext import commands
from replit import Database, db
import qrcode

if db is not None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)


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

def get_embed_color(message):
    """Get color for embeds from json """
    return int(server[str(message.guild.id)]['embed_color'], 16)


class Other(commands.Cog, description='Остальное'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.command(aliases=['рандом'], name='random', description='Выдаёт рандомное число в заданном промежутке', help='[от] [до]')
    async def random_num(self, ctx, arg1, arg2):
        arg1 = int(arg1)
        arg2 = int(arg2)
        num = randint(arg1,arg2)
        await ctx.reply(f'Рандомное число: {num}')

    @commands.command(aliases=['инфо'], description='Выводит информацию об участнике канала', help='[ник]')
    async def info(self, ctx, *, member: discord.Member):
        embed = discord.Embed(title=f'Информация о пользователе {member}', color=get_embed_color(ctx.message))

        member_roles = []
        for role in member.roles:
            if role.name != "@everyone":
                member_roles.append(role.mention)
        member_roles = member_roles[::-1]
        member_roles = ', '.join(member_roles)
        
        emoji_status = get_emoji_status(ctx.message)

        member_status = str(member.status)
        status = {
            'online':'{} В сети'.format(emoji_status['online']),
            'dnd':'{} Не беспокоить'.format(emoji_status['dnd']),
            'idle':'{} Не активен'.format(emoji_status['idle']),
            'offline':'{} Не в сети'.format(emoji_status['offline'])
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


def setup(bot):
    bot.add_cog(Other(bot))