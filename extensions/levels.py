from time import time
from random import randint

import discord
from discord.ext import commands

from extensions.bot_settings import get_db, get_embed_color, get_prefix, is_bot_or_guild_owner
from ._levels import update_member

server = get_db()

class Levels(commands.Cog, description='Cистема уровней'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['levels']

        self.last_user_message = {}
        self.koef = 10


    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.add_member(member)


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if str(member.id) in server[str(member.guild.id)]['users']:
            del server[str(member.guild.id)]['users'][str(member.id)]


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
            
        if (not before.channel) and after.channel:
            if member in after.channel.members:
                server[str(member.guild.id)]['voice_time'][str(member.id)] = int(time())
        elif member not in before.channel.members and (not after.channel):
            try:
                print('DICT', server[str(member.guild.id)]['voice_time'])
                sit_time = int(time()) - server[str(member.guild.id)]['voice_time'][str(member.id)]
                del server[str(member.guild.id)]['voice_time'][str(member.id)]
                exp = (sit_time // 60) * self.koef
                await update_member(member, exp)

                # LOG INTO MY DISCORD GUILD
                print(f'Выдано {member.display_name} {exp} опыта')
                channel = await self.bot.fetch_channel(859816092008316928)
                await channel.send(f'**[LEVELS]** Выдано {member.display_name} {exp} опыта')
            except KeyError as key:
                print('[LEVELS KeyError]', key) 
            except Exception as e:
                print('[LEVELS ERROR]', e)


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if message.content.startswith(get_prefix(message.guild.id)):
                return
            user_id = message.author.id

            if str(user_id) not in server[str(message.guild.id)]['users']:
                await self.add_member(message)
            else:
                xp = randint(10,25)
                await update_member(message, xp)


    async def add_member(self, arg):
        if isinstance(arg, discord.Message):
            member = arg.author
        elif isinstance(arg, discord.Member):
            member = arg

        server[str(member.guild.id)]['users'][str(member.id)] = {}
        userstats = server[str(member.guild.id)]['users'][str(member.id)]

        userstats['xp'] = 0
        userstats['level'] = 0
        if 'on_join_role' in server[str(member.guild.id)]['configuration']:
            userstats['role'] = server[str(member.guild.id)]['configuration']['on_join_role']
            await member.add_roles(member.guild.get_role(userstats['role']))
        else:
            userstats['role'] = ''


    @commands.command(name='clear_lvl', description='', help='', hidden=True)
    @commands.has_guild_permissions(administrator=True)
    async def clear_lvl(self, ctx:commands.Context):
        userstats = server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
        userstats['level'] = 0
        userstats['xp'] = 0
        userstats['role'] = ''

        await ctx.message.add_reaction('✅')


    @commands.command(
        description='Добавляет опыт участнику',
        help='[Участник] [опыт]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def add_xp(self, ctx:commands.Context, member:discord.Member, xp:int):
        await update_member(member, xp)
        await ctx.message.add_reaction('✅')


    @commands.command(
        description='Устанавливает уровень участнику',
        help='[Участник] [уровень]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def set_lvl(self, ctx:commands.Context, member:discord.Member, lvl:int):
        await update_member(member, xp=lvl**4)

        await ctx.message.add_reaction('✅')


    @commands.command(
        name='add_level_role',
        description='Добавляет уровень для роли',
        help='[уровень] [роль]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def add_level_role(self, ctx:commands.Context, level:str, role:discord.Role):
        server[str(ctx.guild.id)]['roles_by_level'][level] = role.id
        await ctx.message.add_reaction('✅')


    @commands.command(
        name='remove_level_role',
        description='Удаляёт уровень для роли',
        help='[уровень]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def remove_level_role(self, ctx:commands.Context, level):
        levels = server[str(ctx.guild.id)]['roles_by_level']
        try:
            del levels[level]
            await ctx.message.add_reaction('✅')
        except KeyError:
            await ctx.reply('Такого уровня не существует!')


    @commands.command(
        name='reset_levels',
        description='Очищает весь список уровней',
        help='',
        hidden=True)
    @commands.is_owner()
    async def reset_levels(self, ctx:commands.Context):
        server[str(ctx.guild.id)]['roles_by_level'] = {}
        await ctx.message.add_reaction('✅')


    @commands.command(
        name='show_info',
        description='Показывает уровневую информацию об участнике сервера',
        help='[участник]')
    async def show_info(self, ctx:commands.Context, member:discord.Member):
        userstats = server[str(ctx.guild.id)]['users'][str(member.id)]
        xp = userstats['xp']
        lvl = userstats['level']
        role_id = userstats['role']
        embed = discord.Embed(color=get_embed_color(ctx.guild.id))
        embed.title=f'Уровневая информация пользователя {member}'
        embed.description = f'`{lvl}-й` уровень, `{xp}` опыта. {ctx.guild.get_role(role_id)}'
        await ctx.send(embed=embed)


    @commands.group(
        name='on_join_role',
        description='Задаёт выдачу стартовой роли новым участникам',
        help='[роль]',
        usage='Только для Администрации',
        invoke_without_command=True)
    @is_bot_or_guild_owner()
    async def on_join_role(self, ctx:commands.Context, role:discord.Role):
        server[str(ctx.guild.id)]['configuration']['on_join_role'] = role.id
        await ctx.message.add_reaction('✅')


    @on_join_role.command(
        name='remove',
        description='Задаёт выдачу стартовой роли новым участникам',
        help='[роль]',
        usage='Только для Владельца сервера')
    @is_bot_or_guild_owner()
    async def on_join_role_remove(self, ctx:commands.Context):
        try:
            del server[str(ctx.guild.id)]['configuration']['on_join_role']
            await ctx.message.add_reaction('✅')
        except KeyError:
            await ctx.reply('Роль не задана!')
        

    @commands.command(
        name='give_everyone_start_role',
        aliases=['gesr'],
        description='Выдаёт начальную роль всем тем, кто её не имеет',
        help='',
        usage='Владельцу Бота или Сервера')
    @is_bot_or_guild_owner()
    async def add_start_role(self, ctx:commands.Context):
        try:
            role_id = server[str(ctx.guild.id)]['configuration']['on_join_role']
            role = ctx.guild.get_role(role_id)
        except Exception as e:
            print('adr', e)
            return

        members = ctx.guild.members
        for member in members:
            if member.bot:
                continue

            try:
                current_role = server[str(ctx.guild.id)]['users'][str(member.id)]['role']
            except KeyError:
                await self.add_member(member)
                continue
            
            if current_role == '':
                server[str(ctx.guild.id)]['users'][str(member.id)]['role'] = role_id
                await member.add_roles(role)


    @commands.command(
        name='remove_user',
        description='Удаляет пользователя из базы',
        help='[участник]',
        hidden=True)
    @is_bot_or_guild_owner()
    async def remove_user(self, ctx:commands.Context, member:discord.Member):
        try:
            del server[str(ctx.guild.id)]['users'][str(member.id)]  
        except KeyError:
            print('Member not found!')


    @commands.command(name='get_levels', description='Показывает весь список уровней по ролям', help='')
    async def get_levels(self, ctx:commands.Context):
        dict_levels = server[str(ctx.guild.id)]['roles_by_level']
        content = ''
        
        for level in dict_levels:
            role = ctx.guild.get_role(dict_levels[level])
            content += f'{level} — {role.mention}\n'

        embed = discord.Embed(description=content, color=get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)

    @commands.command(name='how_much_sit', description='Показывает, сколько времени вы сидите в голосовом канале', help='')
    async def how_much_sit(self, ctx:commands.Context):
        try:
            start_sit = server[str(ctx.guild.id)]['voice_time'][str(ctx.author.id)]
        except KeyError:
            return await ctx.reply('Вы не сидите в голосовом канале!')

        sit_time = int(time() - start_sit) // 60
        await ctx.reply(f'Вы сидите уже `{sit_time}` минут')

    @commands.command(name='update_levels', description='', help='')
    @commands.is_owner()
    async def update_levels(self, ctx:commands.Context):
        server[str(ctx.guild.id)]['voice_time'] = {}

def setup(bot):
    bot.add_cog(Levels(bot))