from time import time
from random import randint

import discord
from discord.ext import commands

from extensions.bot_settings import get_db, get_prefix

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
    async def on_voice_state_update(self, member, before, after):
        if after.channel is not None:
            if member in after.channel.members:
                self.member_voice_time[member.id] = time()
        elif member not in before.channel.members:
            try:
                sit_time = time() - self.member_voice_time[member.id]
                del self.member_voice_time[member.id]
                exp = (int(sit_time) // 60) * self.koef
                await self.update_member(member, exp)
                print(f'Выдано {member.display_name} {exp} опыта')
            except Exception as e:
                print('ERROR', e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if message.content.startswith(get_prefix(message.guild)):
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
        userstats['role'] = ''

    async def update_member(self, arg, xp):
        if isinstance(arg, discord.Message):
            message = arg
            member = message.author
            member_id = str(message.author.id)
            guild_id = str(message.guild.id)
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

        guild_levels = server[str(member.guild.id)]['roles_by_level']
        userstats = server[str(member.guild.id)]['users'][str(member.id)]

        userstats['xp'] += xp
        exp = userstats['xp']
        current_level = userstats['level']
        new_level = exp ** (1/4)

        if current_level < new_level:
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
                
                if from_msg:
                    await message.channel.send(f'{member.mention} получил `{lvl}-й` уровень и повышение до {new_role.mention}', delete_after=30)
                else:
                    await member.send(f'Вы получили `{lvl}-й` уровень и повышение до {str(new_role)}', delete_after=30)
                return
            else:
                if from_msg:
                    await message.channel.send(f'{member.mention} получил `{lvl}-й` уровень', delete_after=15)
                else:
                    await member.send(f'Вы получили `{lvl}-й` уровень', delete_after=15)


    @commands.command(name='clear_lvl', description='', help='')
    @commands.has_guild_permissions(administrator=True)
    async def clear_lvl(self, ctx):
        userstats = server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
        
        userstats['level'] = 0
        userstats['xp'] = 0
        userstats['role'] = ''

    @commands.command(description='Устанавливает опыт участнику', help='[Участник] [опыт]')
    @commands.has_guild_permissions(administrator=True)
    async def set_xp(self, message, member:discord.Member, xp:int):
        userstats = server[str(message.guild.id)]['users'][str(member.id)]
        
        userstats['xp'] = xp
        exp = userstats['xp']
        new_level = exp ** (1/4)

        userstats['level'] = round(new_level)
        lvl = userstats['level']
        await message.channel.send(f'{member.mention} получил {lvl}-й уровень')

    @commands.command(description='Устанавливает уровень участнику', help='[Участник] [уровень]')
    @commands.has_guild_permissions(administrator=True)
    async def set_lvl(self, ctx, member:discord.Member, lvl:int):
        userstats = server[str(ctx.guild.id)]['users'][str(member.id)]
        
        userstats['level'] = lvl
        userstats['xp'] = lvl ** 4

        await ctx.message.add_reaction('✅')

    @commands.command(name='add_level_role', description='Добавляет уровень для роли', help='[уровень] [роль]')
    @commands.has_guild_permissions(administrator=True)
    async def add_level_role(self, ctx, level:str, role:discord.Role):
        server[str(ctx.guild.id)]['roles_by_level'][level] = role.id
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove_level_role', description='Удаляёт уровень для роли', help='[уровень или роль]')
    @commands.has_guild_permissions(administrator=True)
    async def remove_level_role(self, ctx, arg):
        levels = server[str(ctx.guild.id)]['roles_by_level']
        if isinstance(arg, discord.Role):
            level = levels.get(arg.id)
        elif isinstance(arg, str):
            level = arg
        del levels[level]
        await ctx.message.add_reaction('✅')

    @commands.command(name='update', description='Очищает весь список уровней', help=' ')
    @commands.is_owner()
    async def update_db(self, ctx):
        server[str(ctx.guild.id)]['roles_by_level'] = {}
        await ctx.message.add_reaction('✅')

    @commands.command(name='show_lvl', description='Показывает ваш текущий уровень', help=' ')
    async def show_lvl(self, ctx):
        userstats = server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
        xp = userstats['xp']
        lvl = userstats['level']
        await ctx.send(f'У вас `{lvl}-й` уровень и {xp} xp')




def setup(bot):
    bot.add_cog(Levels(bot))