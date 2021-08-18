from main import get_collection
from time import time
from random import randint
import json

import discord
from discord.ext import commands

from ..bot_settings import get_embed_color, get_guild_configuration, get_guild_user, get_guild_users, get_prefix, is_administrator_or_bot_owner
from ._levels import update_member, formula_of_experience



class Levels(commands.Cog, description='Cистема уровней'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

        self.last_user_message = {}
        self.time_factor = 10


    def _get_guild_start_role(self, guild_id):
        guild_conf = get_guild_configuration(guild_id)
        if 'on_join_role' in guild_conf:
            return guild_conf.get('on_join_role')
        else:
            return ''


    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.add_member(member)


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        collection = get_collection(member.guild.id)
        collection.update_one({'_id':'users'}, {'$unset':str(member.id)})


    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if member.bot:
            return
        voice = self.server[str(member.guild.id)]['voice_time']

        if (not before.channel) and after.channel: # * If member join to channel
            members = after.channel.members
            if len(members) == 2:
                voice[str(member.id)] = int(time())

                first_member = members[0]
                if str(first_member.id) not in voice:
                    voice[str(first_member.id)] = int(time())
            elif len(members) > 2:
                voice[str(member.id)] = int(time())

        elif member not in before.channel.members and (not after.channel): # * if member left from channel
            members = before.channel.members
            if len(members) == 1:
                await self.check_time(member, voice)
                first_member = members[0]
                await self.check_time(first_member, voice)
            elif len(members) > 1:
                await self.check_time(member, voice)
        elif member not in before.channel.members and member in after.channel.members: # * If member moved from one channel to another
            before_members = before.channel.members
            after_members = after.channel.members

            if len(before_members) == 0:
                if len(after_members) == 1:
                    return
                elif len(after_members) > 1:
                    if len(after_members) == 2:
                        voice[str(after_members[0].id)] = int(time())
                    voice[str(member.id)] = int(time())

            if len(before_members) == 1:
                await self.check_time(before_members[0], voice)
            if len(after_members) == 1:
                await self.check_time(after_members[0], voice)


    async def check_time(self, member, voice):
        try:
            sit_time = int(time()) - voice[str(member.id)]
            del voice[str(member.id)]
            exp = (sit_time // 60) * self.time_factor
            await update_member(member, exp)

            member_db = self.server[str(member.guild.id)]['users'][str(member.id)]

            if 'voice_time_count' not in member_db:
                member_db['voice_time_count'] = 0
            member_db['voice_time_count'] += (sit_time // 60)
        except Exception as e:
            print('[LEVELS ERROR]', e)


    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author.bot:
            return

        if message.content.startswith(get_prefix(message.guild.id)):
            return
        user_id = message.author.id

        user = get_guild_user(message.guild.id, user_id)

        if user is None:
            await self.add_member(message)
        else:
            xp = randint(25,35)
            await update_member(message, xp)


    async def add_member(self, arg):
        if isinstance(arg, discord.Message):
            member = arg.author
        elif isinstance(arg, discord.Member):
            member = arg

        role = self._get_guild_start_role(member.guild.id)

        user_dict = {
            'voice_time_count':0,
            'leveling': {
                'level':1,
                'xp':0,
                'xp_amount':0,
                'role':role
            }
        }


        collection = get_collection(member.guild.id)
        collection.update_one(
            {'_id':'users'},
            {'$set':{str(member.id):user_dict}},
            upsert=True
        )

        if role != '':
            await member.add_roles(member.guild.get_role(role))


    @commands.command(name='reset_my_stats', description='Обнуляет вашу статистику', help='')
    async def reset_member_statistics(self, ctx:commands.Context):
        user_stats = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
        user_stats['voice_time_count'] = 0

        user_leveling = user_stats['leveling']

        user_leveling['level'] = 1
        user_leveling['xp'] = 0
        user_leveling['xp_amount'] = 0

        current_role = ctx.guild.get_role(user_leveling['role'])
        if current_role:
            await ctx.author.remove_roles(current_role)

        role = self._get_guild_start_role(ctx.guild.id)
        user_leveling['role'] = role
        if role != '':
            await ctx.author.add_roles(ctx.guild.get_role(role))

        await ctx.message.add_reaction('✅')


    @commands.group(name='levels', aliases=['level', 'lvl'], description='Команда для управления Уровнями', help='[команда]', invoke_without_command=True)
    async def levels(self, ctx:commands.Context):
        await ctx.send('Здесь ничего нет :(')


    @levels.command(
        description='Добавляет опыт участнику',
        help='[Участник] [опыт]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def add_xp(self, ctx:commands.Context, member:discord.Member, xp:int):
        await update_member(member, xp)
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='add',
        description='Добавляет уровень для роли',
        help='[уровень] [роль]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def add(self, ctx:commands.Context, level:str, role:discord.Role):
        self.server[str(ctx.guild.id)]['roles_by_level'][level] = role.id
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='remove',
        description='Удаляёт уровень для роли',
        help='[уровень]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def remove(self, ctx:commands.Context, level):
        levels = self.server[str(ctx.guild.id)]['roles_by_level']
        try:
            del levels[level]
            await ctx.message.add_reaction('✅')
        except KeyError:
            await ctx.reply('Такого уровня не существует!')


    @levels.command(
        name='replace',
        description='Заменяет роль уровня на другой уровень',
        help='[старый уровень] [новый уровень]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def replace(self, ctx:commands.Context, old, new):
        roles_by_level = self.server[str(ctx.guild.id)]['roles_by_level']
        try:
            role = roles_by_level[old]
        except KeyError:
            return await ctx.message.add_reaction('❌')
        del roles_by_level[old]
        roles_by_level[new] = role
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='reset',
        description='Очищает весь список уровней',
        help='')
    @is_administrator_or_bot_owner()
    async def reset_levels(self, ctx:commands.Context):
        self.server[str(ctx.guild.id)]['roles_by_level'] = {}
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='list', 
        description='Показывает список ролей по уровню', 
        help='')
    async def list(self, ctx:commands.Context):
        dict_levels = self.server[str(ctx.guild.id)]['roles_by_level']
        content = ''
        
        for level in dict_levels:
            xp_amount = 0
            role = ctx.guild.get_role(dict_levels[level])
            for _level in range(1, int(level)):
              exp = formula_of_experience(_level)
              xp_amount += exp
            content += f'{level} — {role.mention} Необходимо опыта: {xp_amount}\n'

        if content == '':
            content = 'Уровней нет!'

        embed = discord.Embed(description=content, color=get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @levels.group(
        name='set',
        description='Позволяет изменить статистику участнику сервера',
        help='[команда]',
        invoke_without_command=True,
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def set(self, ctx:commands.Context):
        await ctx.send('Здесь ничего нет! Используйте команду `help Levels` для получения информации!')
        

    @set.command(
        name='role',
        description='Устанавливает роль участнику сервера в базе данных',
        help='[участник] [роль]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def role(self, ctx:commands.Context, member:discord.Member, role:discord.Role):
        self.server[str(ctx.guild.id)]['users'][str(member.id)]['leveling']['role'] = role.id
        await ctx.message.add_reaction('✅')


    @set.command(
        name='time',
        description='Устанавливает время участнику сервера в базе данных',
        help='[участник] [время (мин)]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def time(self, ctx:commands.Context, member:discord.Member, time:int):
        self.server[str(ctx.guild.id)]['users'][str(member.id)]['voice_time_count'] = time
        await ctx.message.add_reaction('✅')


    @set.command(
        name='level',
        description='Устанавливает уровень участнику сервера в базе данных',
        help='[участник] [уровень]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def level(self, ctx:commands.Context, member:discord.Member, level:int):
        self.server[str(ctx.guild.id)]['users'][str(member.id)]['leveling']['level'] = level
        await ctx.message.add_reaction('✅')


    @set.command(
        name='xp',
        description='Устанавливает опыт участнику сервера в базе данных',
        help='[участник] [кол-во опыта]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def xp(self, ctx:commands.Context, member:discord.Member, xp:int):
        self.server[str(ctx.guild.id)]['users'][str(member.id)]['leveling']['xp'] = xp
        self.server[str(ctx.guild.id)]['users'][str(member.id)]['leveling']['xp_amount'] = xp
        await ctx.message.add_reaction('✅')


    @commands.command(
        name='show_info',
        description='Показывает уровневую информацию об участнике сервера',
        help='[участник]')
    async def show_info(self, ctx:commands.Context, member:discord.Member):
        userstats = self.server[str(ctx.guild.id)]['users'][str(member.id)]['leveling']
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
    @is_administrator_or_bot_owner()
    async def on_join_role(self, ctx:commands.Context, role:discord.Role):
        self.server[str(ctx.guild.id)]['configuration']['on_join_role'] = role.id
        await ctx.message.add_reaction('✅')


    @on_join_role.command(
        name='remove',
        description='Задаёт выдачу стартовой роли новым участникам',
        help='[роль]',
        usage='Администрация')
    @is_administrator_or_bot_owner()
    async def on_join_role_remove(self, ctx:commands.Context):
        try:
            del self.server[str(ctx.guild.id)]['configuration']['on_join_role']
            await ctx.message.add_reaction('✅')
        except KeyError:
            await ctx.reply('Роль не задана!')


    @commands.command(
        name='give_everyone_start_role',
        aliases=['gesr'],
        description='Выдаёт начальную роль всем тем, кто её не имеет',
        help='',
        usage='Администрация')
    @is_administrator_or_bot_owner()
    async def add_start_role(self, ctx:commands.Context):
        try:
            role_id = self.server[str(ctx.guild.id)]['configuration']['on_join_role']
            role = ctx.guild.get_role(role_id)
        except Exception as e:
            print('adr', e)
            return

        members = ctx.guild.members
        for member in members:
            if member.bot:
                continue

            try:
                current_role = self.server[str(ctx.guild.id)]['users'][str(member.id)]['role']
            except KeyError:
                await self.add_member(member)
                continue
            
            if current_role == '':
                self.server[str(ctx.guild.id)]['users'][str(member.id)]['role'] = role_id
                await member.add_roles(role)


    @commands.command(name='voice_time', description='Показывает, сколько времени вы сидите в голосовом канале', help='')
    async def voice_time(self, ctx:commands.Context):
        try:
            start_sit = self.server[str(ctx.guild.id)]['voice_time'][str(ctx.author.id)]
        except KeyError:
            return await ctx.reply('Вы не сидите в голосовом канале!')
        try:
            all_time = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]['voice_time_count']
        except KeyError:
            all_time = 0

        duration = int(time() - start_sit) // 60
        duration_hours = duration // 60
        duration_minutes = duration % 60
        if duration_hours == 0:
            content = f'Вы сидите `{duration_minutes}` мин. Общее время в головом канале: {all_time+duration}'
        else:
            content = f'Вы сидите `{duration_hours}` час. `{duration_minutes}` мин. Общее время в головом канале: {all_time+duration}'
        await ctx.reply(content)

    @commands.command(
        name='clear_members_stats',
        description='Удаляет уровневую статистику всех пользователей на сервере',
        help='',
        usage='Администрация')
    @is_administrator_or_bot_owner()
    async def clear_members_stats(self, ctx:commands.Context):
        members = ctx.guild.members
        if 'on_join_role' in self.server[str(ctx.guild.id)]['configuration']:
            role = self.server[str(ctx.guild.id)]['configuration']['on_join_role']
        else:
            role = ''

        for member in members:
            if member.bot:
                continue
            self.server[str(ctx.guild.id)]['users'][str(member.id)]['leveling'] = {
                'level':1,
                'xp':0,
                'xp_amount':0,
                'role':role,
            }
            if role != '':
                await member.add_roles(ctx.guild.get_role(role))

        await ctx.message.add_reaction('✅')