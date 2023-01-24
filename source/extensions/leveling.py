from collections import defaultdict
from random import randint
from time import time

from interactions import Choice, Color, Embed, Extension, Member, Message, Permissions, Role, option

from core import Asteroid, BotException, MissingPermissions, command, listener
from core.context import CommandContext
from core.database.models import GuildData, GuildUser, GuildUserLeveling
from utils import try_run

COOLDOWN = 10
MINIMUM_EXP = 10
MAXIMUM_EXP = 30


def get_current_timestamp() -> int:
    return int(time())


def get_random_experience() -> int:
    return randint(MINIMUM_EXP, MAXIMUM_EXP)


class Leveling(Extension):
    def __init__(self, client):
        self.client: Asteroid = client
        self.cooldowns: defaultdict[tuple[str, str], int] = defaultdict(lambda: 0)

    @listener
    async def on_message_create(self, message: Message):
        if message.author.bot:
            return

        guild_data = await self.client.database.get_guild(message.guild_id)
        if not guild_data.leveling:
            return
        user_data = await self.client.database.get_user(message.guild_id, message.author.id)

        if self._is_cooldown(message):
            return

        await self._increase_exp(guild_data, user_data, get_random_experience())
        self.cooldowns[(str(message.guild_id), str(message.author.id))] = get_current_timestamp()

    def get_user_cooldown(self, user: Member) -> int:
        return self.cooldowns[(str(user.guild_id), str(user.id))]

    def _is_cooldown(self, message: Message) -> bool:
        user_cooldown = self.get_user_cooldown(message.member)
        return get_current_timestamp() - user_cooldown <= COOLDOWN

    @staticmethod
    def calculate_experience_for_level(level: int) -> int:
        return int((100 * level) ** 1.2)

    async def _increase_exp(self, guild_data: GuildData, user_data: GuildUser, exp: int):
        user_leveling = user_data.leveling

        user_leveling.xp += exp
        user_leveling.xp_amount += exp
        exp_to_next_level: int = self.calculate_experience_for_level(user_leveling.level + 1)
        role_to_add: int = None  # type: ignore

        while user_leveling.xp >= exp_to_next_level:
            user_leveling.xp -= exp_to_next_level
            user_leveling.level += 1
            exp_to_next_level = self.calculate_experience_for_level(user_leveling.level + 1)

            if role_id := guild_data.leveling.roles_by_level.get(user_leveling.level):
                role_to_add = role_id

        if role_to_add is not None:
            member = await self.client.get_member(user_data.guild_id, user_data.id)
            await self._add_level_role_to_user(member, role_to_add, user_leveling)

        await user_data.update()

    @staticmethod
    async def _add_level_role_to_user(
        member: Member, role_id: int, user_leveling: GuildUserLeveling
    ):
        if user_leveling.role is not None:
            await try_run(member.remove_role, user_leveling.role, guild_id=member.guild_id)
        await try_run(member.add_role, role_id, guild_id=member.guild_id)
        user_leveling.role = role_id

    @command()
    async def leveling(self, ctx: CommandContext):
        """Base command for leveling"""

    @leveling.subcommand()
    async def leaderboard(self, ctx: CommandContext):
        """Shows server's leaderboard"""

    @leveling.subcommand()
    @option("The member for increase experience of")
    @option("The amount of experience", min_value=0, autocomplete=True)
    async def add_xp(self, ctx: CommandContext, member: Member, exp: int):
        """Increases member's experience"""

    @leveling.subcommand()
    async def wipe_statistics(self, ctx: CommandContext):
        """Wipes statistics of all members"""

    @command()
    async def level_roles(self, ctx: CommandContext):
        """Base command for level roles"""

    @level_roles.subcommand()
    @option("The role")
    async def set_start_role(self, ctx: CommandContext, role: Role = None):
        """Adds a start role on this server. Empty to remove"""

    @level_roles.subcommand()
    @option("The level", min_value=1)
    @option("The role for level")
    async def add_role(self, ctx: CommandContext, level: int, role: Role):
        """Adds a new level role"""
        if not ctx.has_permissions(Permissions.MANAGE_GUILD):
            raise MissingPermissions(Permissions.MANAGE_GUILD)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        roles_by_level = guild_data.leveling.roles_by_level

        _level = str(level)
        if _level in roles_by_level:
            raise BotException("LEVEL_ROLE_ALREADY_TAKEN")

        roles_by_level[_level] = int(role.id)
        await guild_data.leveling.update()

        translate = ctx.translate("LEVEL_ROLE_ADDED")
        await ctx.send(translate, ephemeral=True)

    @level_roles.subcommand()
    @option("The level", min_value=1, autocomplete=True)
    async def remove_role(self, ctx: CommandContext, level: int):
        """Removes a level role"""
        if not ctx.has_permissions(Permissions.MANAGE_GUILD):
            raise MissingPermissions(Permissions.MANAGE_GUILD)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        roles_by_level = guild_data.leveling.roles_by_level

        _level = str(level)
        if _level not in roles_by_level:
            raise BotException("LEVEL_ROLE_NOT_FOUND")

        roles_by_level.pop(_level)
        await guild_data.leveling.update()

        translate = ctx.translate("LEVEL_ROLE_REMOVED")
        await ctx.send(translate, ephemeral=True)

    @level_roles.autocomplete("level")
    async def autocomplete_level(self, ctx: CommandContext, user_input: str):
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        roles_by_level = guild_data.leveling.roles_by_level.items()
        return [
            Choice(name=str(level), value=level)
            for level in roles_by_level
            if str(level).startswith(user_input)
        ]

    @level_roles.subcommand(name="list")
    async def level_roles_list(self, ctx: CommandContext):
        """Shows all level roles on this server"""
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        roles_by_level = guild_data.leveling.roles_by_level

        embed = Embed(
            title=ctx.get_translate("LEVEL_ROLES_LIST_EMBED_TITLE"),
            description="",
            color=Color.BLURPLE,
        )

        for level, role_id in roles_by_level.items():
            embed.description += f"**` {level} `** <@&{role_id}>"

        await ctx.send(embeds=embed)

    @level_roles.subcommand()
    async def reset_level_roles(self, ctx: CommandContext):
        """Resets level roles"""


def setup(client):
    Leveling(client)
