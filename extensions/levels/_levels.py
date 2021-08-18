from time import time

import discord
from ..bot_settings import get_collection, get_guild_level_roles, get_guild_user

last_user_message = {}

async def update_member(arg, exp):
    """Method for giving exp for guild member"""
    guild_id = str(arg.guild.id)

    if isinstance(arg, discord.Message):
        message = arg
        member = message.author
        if check_timeout(guild_id, member):
            return
    elif isinstance(arg, discord.Member):
        member = arg

    member_stats = get_guild_user(member.guild.id, member.id)['leveling']
    xp = member_stats['xp'] + exp
    xp_amount = member_stats['xp_amount'] + exp

    collection = get_collection(member.guild.id)
    collection.update_one(
        {'_id':'users'},
        {'$set':{f'{str(member.id)}.leveling.xp':xp}})

    collection.update_one(
        {'_id':'users'},
        {'$set':{f'{str(member.id)}.leveling.xp_amount':xp_amount}})

    exp_to_next_level = formula_of_experience(member_stats['level'])
    while member_stats['xp'] > exp_to_next_level:
        level = member_stats['level'] + 1
        xp -= exp_to_next_level
        collection.update_one(
        {'_id':'users'},
        {'$set':{f'{str(member.id)}.leveling.level':level}})

        collection.update_one(
        {'_id':'users'},
        {'$set':{f'{str(member.id)}.leveling.xp':xp}})

        member_stats = get_guild_user(member.guild.id, member.id)['leveling']

        exp_to_next_level = formula_of_experience(member_stats['level'])

        guild_levels = get_guild_level_roles(member.guild.id)
        new_role = member.guild.get_role(guild_levels.get(str(member_stats['level'])))

        if new_role is not None:
            await update_member_role(guild_id, member, new_role)
            await notify_member(arg.guild, member, member_stats['level'], new_role)


def formula_of_experience(level:int):
    return int(((level+1) * 100) + (((level+1) * 20) ** 1.4))


def check_timeout(guild_id, member):
    guild_id = str(guild_id)
    member_id = str(member.id)

    if guild_id not in last_user_message:
        last_user_message[guild_id] = {}

    if member_id in last_user_message[guild_id]:
        last_msg_time = last_user_message[guild_id][member_id]
        current_time = time()
        if current_time - last_msg_time < 10:
            return True
    else:
        last_user_message[guild_id][member_id] = time()
    return False


async def update_member_role(guild_id, member, new_role):
    member_stats = get_guild_user(guild_id, member.id)['leveling']
    old_role = member_stats['role']

    for role in member.roles:
        if role.id == old_role:
            await member.remove_roles(role, reason='Удаление старого уровня')
            break
    await member.add_roles(new_role, reason='Повышение уровня')
    collection = get_collection(guild_id)
    collection.update_one({'_id':'users'}, {'$set':{f'{str(member.id)}.leveling.role':new_role.id}})


async def notify_member(guild, member, new_level, new_role=None):
    system_channel = guild.system_channel
    if new_role:
        if system_channel:
            await system_channel.send(f'{member.mention} получил `{new_level}-й` уровень и повышение до {new_role.mention}', delete_after=15)
        else:
            await member.send(f'Вы получили `{new_level}-й` уровень и повышение до {str(new_role)}', delete_after=15)
