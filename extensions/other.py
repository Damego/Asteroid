import discord
from discord.ext import commands
import json
import os
from replit import Database, db
from random import randint
import qrcode

if db != None:
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




class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        
    @commands.command(aliases=['рандом'], name='random', description='Выдаёт рандомное число в заданном промежутке')
    async def random_num(self, ctx, arg1, arg2):
        arg1 = int(arg1)
        arg2 = int(arg2)
        num = randint(arg1,arg2)
        await ctx.reply(f'Рандомное число: {num}')

    
    @commands.command(aliases=['инфо'], description='Выводит информацию об участнике канала')
    async def info(self, ctx, *, member: discord.Member):
        embed = discord.Embed(title=f'Информация о пользователе {member}', color = get_embed_color(ctx.message))

        stats = get_stats(ctx.message, member)
        lvl = stats['lvl']
        xp = stats['xp']

        member_roles_names = []
        for role in member.roles:
            if role.name != "@everyone":
                member_roles_names.append(role.mention)
        member_roles_names = ', '.join(member_roles_names)
        
        ls = get_emoji_status(ctx.message)
        member_status = str(member.status)

        if member_status == 'online':
            member_status = '{} В сети'.format(ls['online'])
        elif member_status == 'dnd':
            member_status = '{} Не беспокоить'.format(ls['dnd'])
        elif member_status == 'idle':
            member_status = '{} Не активен'.format(ls['idle'])
        elif member_status == 'offline':
            member_status = '{} Не в сети'.format(ls['offline'])

        embed.add_field(name= "Основная информация:" ,value=f"""
            **Дата регистрации в Discord:** {member.created_at.strftime("%#d %B %Y")}
            **Дата присоединения на сервер:** {member.joined_at.strftime("%#d %B %Y")}
            **Текущий статус:** {member_status}
            **Роли:** {member_roles_names}
            """, inline=False)

        embed.add_field(name='Уровень:', value=lvl)
        embed.add_field(name='Опыт:', value=f'{xp}/{lvl ** 4}')

        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)


    @commands.command(name='qr', aliases=['QR', 'код'], description='Создаёт QR-код')
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


    @commands.command(aliases=['реши'], description='Решает простой матемаический пример')
    async def exercise(self, ctx, arg):
        exercise = arg
        try:
            exercise = eval(exercise)
            await ctx.send(exercise)
        except Exception:
            await ctx.send('Указаны неверные числа/действие!!!')
        

def setup(bot):
    bot.add_cog(Other(bot))