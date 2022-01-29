from time import time
from typing import Union

from discord import Member, Message, Guild, Role

from my_utils import AsteroidBot
from my_utils.languages import get_content

last_user_message = {}


async def update_member(
    bot: AsteroidBot, member_or_message: Union[Member, Message], exp: int
):
    guild = member_or_message.guild
    guild_id = guild.id

    if isinstance(member_or_message, Message):
        message = member_or_message
        member = message.author
        if check_timeout(guild_id, member):
            return
    elif isinstance(member_or_message, Member):
        member = member_or_message

    guild_users_collection = bot.get_guild_users_collection(guild_id)
    member_stats = guild_users_collection.find_one({"_id": str(member.id)})["leveling"]

    xp = member_stats["xp"] + exp
    xp_amount = member_stats["xp_amount"] + exp
    level = member_stats["level"]

    guild_users_collection.update_one(
        {"_id": str(member.id)},
        {"$set": {"leveling.xp": xp, "leveling.xp_amount": xp_amount}},
    )

    exp_to_next_level = formula_of_experience(member_stats["level"])
    while xp > exp_to_next_level:
        level += 1
        xp -= exp_to_next_level

        guild_users_collection.update_one(
            {"_id": str(member.id)},
            {"$set": {"leveling.level": level, "leveling.xp": xp}},
        )

        exp_to_next_level = formula_of_experience(level)

        main_collection = bot.get_guild_main_collection(guild_id)
        roles = main_collection.find_one({"_id": "roles_by_level"})
        if roles is None:
            continue

        role_id = roles.get(str(level))
        new_role = guild.get_role(role_id)
        if new_role is not None:
            lang = bot.get_guild_bot_lang(guild_id)
            content = get_content("LEVELS", lang)["FUNC_UPDATE_MEMBER"]
            await update_member_role(bot, guild_id, member, new_role)
            await notify_member(
                content, guild, member, member_stats["level"], new_role, message
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


async def update_member_role(
    bot: AsteroidBot, guild_id: int, member: Member, new_role: Role
):
    guild_users_collection = bot.get_guild_users_collection(guild_id)
    member_stats = guild_users_collection.find_one({"_id": str(member.id)})["leveling"]
    old_role = member_stats["role"]

    for role in member.roles:
        if role.id == old_role:
            await member.remove_roles(role, reason="Removing old role")
            break
    await member.add_roles(new_role, reason="Adding new role")
    guild_users_collection.update_one(
        {"_id": str(member.id)}, {"$set": {"leveling.role": new_role.id}}
    )


async def notify_member(
    content,
    guild: Guild,
    member: Member,
    new_level: int,
    new_role: Role = None,
    message: Message = None,
):
    desc = content["NOTIFY_GUILD_CHANNEL"].format(
        member=member.mention, level=new_level, role=new_role
    )

    system_channel = guild.system_channel
    if message is not None:
        await message.channel.send(desc, delete_after=15)
    elif system_channel is not None:
        await system_channel.send(desc, delete_after=15)
    else:
        desc = content["NOTIFY_DM"].format(
            member=member.mention, level=new_level, role=new_role
        )
        await member.send(desc, delete_after=15)
