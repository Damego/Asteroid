from time import time
from typing import Union

from discord import Guild, Member, Message, Role
from utils import AsteroidBot, GuildUser, get_content

last_user_message = {}


async def update_member(bot: AsteroidBot, member_or_message: Union[Member, Message], exp: int):
    guild = member_or_message.guild
    guild_id = guild.id
    message = None

    if isinstance(member_or_message, Message):
        message = member_or_message
        member = message.author
        if check_timeout(guild_id, member):
            return
    else:
        member = member_or_message

    guild_data = await bot.get_guild_data(member_or_message.guild.id)
    user_data = await guild_data.get_user(member.id)

    user_xp = user_data.leveling.xp + exp
    xp_amount = user_data.leveling.xp_amount + exp
    level = user_data.leveling.level

    exp_to_next_level = formula_of_experience(level)
    role = None
    roles_by_level = guild_data.roles_by_level

    while user_xp >= exp_to_next_level:
        level += 1
        user_xp -= exp_to_next_level
        exp_to_next_level = formula_of_experience(level)

        role_id = roles_by_level.get(str(level))
        if _role := guild.get_role(role_id):
            role = _role

    if role is not None:
        await update_member_role(user_data, member, role)
        await notify_member(guild_data.configuration.language, guild, member, level, role, message)

    await user_data.set_leveling(
        level=level, xp=user_xp, xp_amount=xp_amount, role_id=role.id if role else None
    )


def formula_of_experience(level: int):
    return int(((level + 1) * 100) + (((level + 1) * 20) ** 1.4))


def check_timeout(guild_id: int, member: Member):
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


async def update_member_role(user_data: GuildUser, member: Member, role: Role):
    old_role_id = user_data.leveling.role

    for member_role in member.roles:
        if member_role.id == old_role_id:
            await member.remove_roles(member_role, reason="Removing old role")
            break
    await member.add_roles(role, reason="Adding new role")


async def notify_member(
    language: str,
    guild: Guild,
    member: Member,
    level: int,
    role: Role = None,
    message: Message = None,
):
    content = get_content("LEVELS", language)["FUNC_UPDATE_MEMBER"]
    desc = content["NOTIFY_GUILD_CHANNEL"].format(member=member.mention, level=level, role=role)

    system_channel = guild.system_channel
    if message is not None:
        await message.channel.send(desc, delete_after=15)
    elif system_channel is not None:
        await system_channel.send(desc, delete_after=15)
    else:
        desc = content["NOTIFY_DM"].format(member=member.mention, level=level, role=role)
        await member.send(desc, delete_after=15)
