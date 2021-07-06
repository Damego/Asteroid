from time import time
from random import randint
from typing import Awaitable

import discord
from discord.ext import commands

from extensions.bot_settings import get_db, get_embed_color, get_prefix, is_bot_or_guild_owner

server = get_db()

class Levels(commands.Cog, description='Cистема уровней'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['levels']

        self.member_voice_time = {}
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
                self.member_voice_time[member.id] = time()
        elif member not in before.channel.members and (not after.channel):
            try:
                sit_time = time() - self.member_voice_time[member.id]
                del self.member_voice_time[member.id]
                exp = (int(sit_time) // 60) * self.koef
                await self.update_member(member, exp)

                # LOG INTO MY DISCORD GUILD
                print(f'Выдано {member.display_name} {exp} опыта')
                channel = await self.bot.fetch_channel(859816092008316928)
                await channel.send(f'**[LEVELS]** Выдано {member.display_name} {exp} опыта')
            except Exception as e:
                print('[LEVELS ERROR]', e)


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if message.content.startswith(get_prefix(message.guild.id)):
                return
            user_id = message.author.id

            if not str(user_id) in server[str(message.guild.id)]['users']:
                await self.add_member(message)
            else:
                xp = randint(10,25)
                await self.update_member(message, xp)


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


    async def update_member(self, arg, xp):
        guild_id = str(arg.guild.id)
        if isinstance(arg, discord.Message):
            message = arg
            member = message.author
            member_id = str(member.id)
            from_msg = True

            if not guild_id in self.last_user_message:
                self.last_user_message[guild_id] = {}

            if member_id in self.last_user_message[guild_id]:
                last_msg_time = self.last_user_message[guild_id][member_id]
                current_time = time()
                if current_time - last_msg_time < 30:
                    return
                
            if not member_id in self.last_user_message[guild_id]:
                self.last_user_message[guild_id][member_id] = time()

        elif isinstance(arg, discord.Member):
            member = arg
            from_msg = False

        guild_levels = server[guild_id]['roles_by_level']
        userstats = server[guild_id]['users'][str(member.id)]

        userstats['xp'] += xp
        exp = userstats['xp']
        current_level = userstats['level']
        new_level = exp ** (1/4)

        if current_level < new_level: # ? while loop
            userstats['level'] += 1
            lvl = userstats['level']
            
            old_role = userstats['role']

            new_role = guild_levels.get(str(lvl))
            new_role = member.guild.get_role(new_role)

            if new_role is not None:
                for role in member.roles:
                    if role.id == old_role:
                        await member.remove_roles(role, reason='Удаление старого уровня')
                        break
                await member.add_roles(new_role, reason='Повышение уровня')
                userstats['role'] = new_role.id
                

                # ! SEND MESSAGE FUNCTION
                if from_msg:
                    await message.channel.send(f'{member.mention} получил `{lvl}-й` уровень и повышение до {new_role.mention}', delete_after=30)
                else:
                    await member.send(f'Вы получили `{lvl}-й` уровень и повышение до {str(new_role)}', delete_after=30) # ? Remove this?
                return
            else:
                if from_msg:
                    await message.channel.send(f'{member.mention} получил `{lvl}-й` уровень', delete_after=15)
                else:
                    await member.send(f'Вы получили `{lvl}-й` уровень', delete_after=15) # ? Remove this?


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
        await self.update_member(member, xp)


    @commands.command(
        description='Устанавливает уровень участнику',
        help='[Участник] [уровень]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def set_lvl(self, ctx:commands.Context, member:discord.Member, lvl:int):
        userstats = server[str(ctx.guild.id)]['users'][str(member.id)]
        userstats['level'] = lvl
        userstats['xp'] = lvl ** 4

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
        name='add_to_all_start_role',
        description='Выдаёт начальную роль всем тем, кто её не имеет',
        help='',
        hidden=True)
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


def setup(bot):
    bot.add_cog(Levels(bot))