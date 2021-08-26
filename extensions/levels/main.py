from time import time
from random import randint

import discord
from discord.ext import commands
from pymongo.collection import Collection

from mongobot import MongoComponentsBot
from ..bot_settings import (
    is_administrator_or_bot_owner,
)
from ._levels import update_member, formula_of_experience



class Levels(commands.Cog, description='Cистема уровней'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = 863677232239869964

        self.last_user_message = {}
        self.time_factor = 10


    def _get_guild_start_role(self, guild_id):
        guild_configuration_collection = self.bot.get_guild_configuration_collection(guild_id)
        guild_configuration = guild_configuration_collection.find_one({'_id':'configuration'})

        if 'on_join_role' in guild_configuration:
            return guild_configuration.get('on_join_role')
        else:
            return ''


    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.add_member(member)


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        collection = self.bot.get_guild_users_collection(member.guild.id)
        collection.delete_one({'_id':str(member.id)})


    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if member.bot:
            return
        
        voice_collection = self.bot.get_guild_voice_time_collection(member.guild.id)

        if (not before.channel) and after.channel: # * If member join to channel
            members = after.channel.members
            if len(members) == 2:
                voice_collection.update_one(
                    {'_id':str(member.id)},
                    {'$set':{'voice_time':time()}},
                    upsert=True
                )

                first_member = members[0]
                if voice_collection.find_one({'_id':str(first_member.id)}) is None:
                    voice_collection.update_one(
                    {'_id':str(first_member.id)},
                    {'$set':{'voice_time':time()}},
                    upsert=True
                )
            elif len(members) > 2:
                voice_collection.update_one(
                    {'_id':str(member.id)},
                    {'$set':{'voice_time':time()}},
                    upsert=True
                )

        elif member not in before.channel.members and (not after.channel): # * if member left from channel
            members = before.channel.members
            if len(members) == 1:
                await self.check_time(member, voice_collection)
                first_member = members[0]
                await self.check_time(first_member, voice_collection)
            elif len(members) > 1:
                await self.check_time(member, voice_collection)
        elif member not in before.channel.members and member in after.channel.members: # * If member moved from one channel to another
            before_members = before.channel.members
            after_members = after.channel.members

            if len(before_members) == 0:
                if len(after_members) == 1:
                    return
                elif len(after_members) > 1:
                    if len(after_members) == 2:
                        voice_collection.update_one(
                            {'_id':str(after_members[0].id)},
                            {'$set':{'voice_time':time()}},
                            upsert=True
                        )
                    voice_collection.update_one(
                        {'_id':str(member.id)},
                        {'$set':{'voice_time':time()}},
                        upsert=True
                    )

            if len(before_members) == 1:
                await self.check_time(before_members[0], voice_collection)
            if len(after_members) == 1:
                await self.check_time(after_members[0], voice_collection)


    async def check_time(self, member, voice_collection: Collection):
        try:
            voice_user = voice_collection.find_one({'_id':str(member.id)})
            sit_time = int(time()) - voice_user['voice_time']
            voice_collection.delete_one({'_id':str(member.id)})
            exp = (sit_time // 60) * self.time_factor
            await update_member(member, exp)

            collection = self.bot.get_guild_users_collection(member.guild.id)
            member_db = collection.find_one({'_id':str(member.id)})

            if member_db.get('voice_time_count') is None:
                collection.update_one(
                    {'_id':str(member.id)},
                    {'$set':{'voice_time_count':0}},
                    upsert=True
                )
            collection.update_one(
                {'_id':str(member.id)},
                {'$inc':{'voice_time_count':(sit_time // 60)}}
                )
        except Exception as e:
            print('[LEVELS ERROR]', e)


    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author.bot:
            return
        if message.content.startswith(self.bot.get_guild_prefix(message.guild.id)):
            return

        user_id = message.author.id

        users_collection = self.bot.get_guild_users_collection(message.guild.id)
        user = users_collection.find_one({'_id':str(user_id)})

        if user is None:
            await self.add_member(message.author)
        else:
            xp = randint(25,35)
            await update_member(self.bot, message, xp)


    async def add_member(self, member):
        role = self._get_guild_start_role(member.guild.id)

        collection = self.bot.get_guild_users_collection(member.guild.id)
        collection.update_one(
            {'_id':str(member.id)},
            {'$set':{
            'voice_time_count':0,
            'leveling': {
                'level':1,
                'xp':0,
                'xp_amount':0,
                'role':role
            }
        }},
            upsert=True
        )

        if role != '':
            await member.add_roles(member.guild.get_role(role))


    @commands.command(name='reset_my_stats', description='Обнуляет вашу статистику', help='')
    async def reset_member_statistics(self, ctx:commands.Context):
        user_id = str(ctx.author.id)
        users = self.bot.get_guild_users_collection(ctx.guild.id)
        user_db = users.find_one({'_id':user_id})

        current_role = ctx.guild.get_role(user_db['leveling']['role'])
        if current_role:
            await ctx.author.remove_roles(current_role)
        role_id = self._get_guild_start_role(ctx.guild.id)

        users.update_one(
            {'_id':user_id},
            {'$set':{
                'voice_time_count':0,
                'leveling': {
                    'level':1,
                    'xp':0,
                    'xp_amount':0,
                    'role':role_id
                    }
                }
            },
        upsert=True)
    
        if role_id:
            await ctx.author.add_roles(ctx.guild.get_role(role_id))

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
        collection = self.bot.get_guild_level_roles_collection(ctx.guild.id)
        collection.update_one(
            {'_id':level},
            {'$set':{'role_id':role.id}},
            upsert=True)
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='remove',
        description='Удаляёт уровень для роли',
        help='[уровень]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def remove(self, ctx:commands.Context, level:str):
        level_roles_collection = self.bot.get_guild_level_roles_collection(ctx.guild.id)
        try:
            level_roles_collection.delete_one({'_id':level})
            await ctx.message.add_reaction('✅')
        except Exception:
            await ctx.reply('Такого уровня не существует!')


    @levels.command(
        name='replace',
        description='Заменяет роль уровня на другой уровень',
        help='[старый уровень] [новый уровень]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def replace(self, ctx:commands.Context, old_level, new_level):
        level_roles_collection = self.bot.get_guild_level_roles_collection(ctx.guild.id)
        role = level_roles_collection.find_one_and_delete({'_id':old_level})['role_id']
        level_roles_collection.update_one(
            {'_id':new_level},
            {'$set':{'role_id':role}},
            upsert=True)
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='reset',
        description='Очищает весь список уровней',
        help='')
    @is_administrator_or_bot_owner()
    async def reset_levels(self, ctx:commands.Context):
        level_roles_collection = self.bot.get_guild_level_roles_collection(ctx.guild.id)
        level_roles_collection.drop_indexes()
        await ctx.message.add_reaction('✅')


    @levels.command(
        name='list',
        description='Показывает список ролей по уровню',
        help='')
    async def list(self, ctx:commands.Context):
        collection = self.bot.get_guild_level_roles_collection(str(ctx.guild.id))
        dict_levels = collection.find()

        content = ''
        
        for level in dict_levels:
            xp_amount = 0
            role = ctx.guild.get_role(level['role_id'])
            for _level in range(1, int(level['_id'])):
              exp = formula_of_experience(_level)
              xp_amount += exp
            content += f'{level["_id"]} — {role.mention} Необходимо опыта: {xp_amount}\n'

        if content == '':
            content = 'Ролей по уровням нет!'

        embed = discord.Embed(description=content, color=self.bot.get_embed_color(ctx.guild.id))
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
        collection = self.bot.get_guild_users_collection(ctx.guild.id)
        collection.update_one(
            {'_id':str(member.id)},
            {'$set':{
                'leveling.role':role.id
            }}
        )
        await ctx.message.add_reaction('✅')


    @set.command(
        name='time',
        description='Устанавливает время участнику сервера в базе данных',
        help='[участник] [время (мин)]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def time(self, ctx:commands.Context, member:discord.Member, time:int):
        collection = self.bot.get_guild_users_collection(ctx.guild.id)
        collection.update_one(
            {'_id':str(member.id)},
            {'$set':{
                'voice_time_count':time
            }}
        )
        await ctx.message.add_reaction('✅')


    @set.command(
        name='level',
        description='Устанавливает уровень участнику сервера в базе данных',
        help='[участник] [уровень]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def level(self, ctx:commands.Context, member:discord.Member, level:int):
        collection = self.bot.get_guild_users_collection(ctx.guild.id)
        collection.update_one(
            {'_id':str(member.id)},
            {'$set':{
                'leveling.level':level
            }}
        )
        await ctx.message.add_reaction('✅')


    @commands.command(
        name='show_info',
        description='Показывает уровневую информацию об участнике сервера',
        help='[участник]')
    async def show_info(self, ctx:commands.Context, member:discord.Member):
        collection = self.bot.get_guild_users_collection(ctx.guild.id)
        userstats = collection.find_one({'_id':str(member.id)})['leveling']
        xp = userstats['xp']
        lvl = userstats['level']
        role_id = userstats['role']
        embed = discord.Embed(color=self.bot.get_embed_color(ctx.guild.id))
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
        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one(
            {'_id':'configuration'},
            {'$set':{'on_join_role':role.id}},
            upsert=True)
        await ctx.message.add_reaction('✅')


    @on_join_role.command(
        name='remove',
        description='Удаляет выдачу стартовой роли новым участникам',
        help='[роль]',
        usage='Администрация')
    @is_administrator_or_bot_owner()
    async def on_join_role_remove(self, ctx:commands.Context):
        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one(
            {'_id':'configuration'},
            {'$unset':'on_join_role'},
        )
        await ctx.message.add_reaction('✅')


    @commands.command(
        name='give_everyone_start_role',
        aliases=['gesr'],
        description='Выдаёт начальную роль всем тем, кто её не имеет',
        help='',
        usage='Администрация')
    @is_administrator_or_bot_owner()
    async def add_start_role(self, ctx:commands.Context):
        guild_configuration_collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        try:
            role_id = guild_configuration_collection.find_one({'_id':'configuration'})['on_join_role']
            role = ctx.guild.get_role(role_id)
        except Exception as e:
            print('adr', e)
            return

        guild_users_collection = self.bot.get_guild_users_collection(ctx.guild.id)

        members = ctx.guild.members
        for member in members:
            if member.bot:
                continue

            current_role = guild_users_collection.find_one({'_id':str(member.id)})['leveling']['role']
            if current_role is None:
                await self.add_member(member)
                continue
            
            if current_role == '':
                guild_users_collection.update_one(
                    {'_id':str(member.id)},
                    {'$set':{'leveling.role':role_id}}
                )
                await member.add_roles(role)


    @commands.command(
        name='clear_members_stats',
        description='Удаляет уровневую статистику всех пользователей на сервере',
        help='',
        usage='Администрация')
    @is_administrator_or_bot_owner()
    async def clear_members_stats(self, ctx:commands.Context):
        members = ctx.guild.members
        guild_configuration_collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        guild_users_collection = self.bot.get_guild_users_collection(ctx.guild.id)

        configuration = guild_configuration_collection.find_one({'_id':'configuration'})
        role = configuration.get('on_join_role')
        if role is None:
            role = ''

        for member in members:
            if member.bot:
                continue

            guild_users_collection.update_one(
                {'_id':str(member.id)},
                {'$set':{
                    'leveling.level':1,
                    'leveling.xp':0,
                    'leveling.xp_amount':0,
                    'leveling.role':role
                    }})

            if role:
                await member.add_roles(ctx.guild.get_role(role))

        await ctx.message.add_reaction('✅')