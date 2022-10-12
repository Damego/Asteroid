from time import time
from collections import defaultdict
from random import randint

from interactions import Extension, Message, CommandContext, option, Member, Role

from core import Asteroid, command, listener, GuildUser


COOLDOWN = 10


class Leveling(Extension):
    def __init__(self, client):
        self.client: Asteroid = client
        self.cooldowns: dict[tuple[int, int], int] = defaultdict(lambda: int(time()))

    @listener
    async def on_message_create(self, message: Message):
        if message.author.bot:
            return
        
        guild_data = await self.client.database.get_guild(message.guild_id)
        if not guild_data.leveling or not guild_data.leveling.message_xp_range:
            return
        user_data = await self.client.database.get_user(message.get_guild, message.author.id)

        if self._is_cooldown(message):
            return
        
        await self._increate_exp(user_data, randint(*guild_data.leveling.message_xp_range))

    def _is_cooldown(self, message: Message):
        return int(time()) - self.cooldowns[(str(message.guild_id), str(message.author.id))] <= COOLDOWN

    def _get_level_xp(self, level: int):
        return int((100 * level) ** 1.2)

    async def _increate_exp(self, user_data: GuildUser, exp: int):
        user_leveling = user_data.leveling
        user_leveling.exp += exp
        exp_to_next_level = self._get_level_xp(user_leveling.level + 1)

        # TODO:
        #   1. Add exp to member
        #   2. Increase level if needed ->
        #       2.1. Give role if needed
        #       2.2. Notify member
        #   3. Update user in db 
        #   4. Add user to cooldown


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

    @leveling.subcommand(name="reset")
    async def reset_stats(self, ctx: CommandContext):
        """Resets statistics of all members"""

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
        # TODO:
        #   Check if role is taken

    @level_roles.subcommand()
    @option("The level", min_value=1, autocomplete=True)
    async def remove_role(self, ctx: CommandContext, level: int):
        """Removes a level role"""

    @level_roles.subcommand(name="list")
    async def level_roles_list(self, ctx: CommandContext):
        """Shows all level roles on this server"""

    @level_roles.subcommand(name="reset")
    async def reset_level_roles(self, ctx: CommandContext):
        """Resets level roles"""


def setup(client):
    Leveling(client)
