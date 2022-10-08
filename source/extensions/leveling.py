from interactions import Extension, Message, CommandContext, option, Member, Role

from core import Asteroid, command, listener


class Leveling(Extension):
    def __init__(self, client):
        self.client: Asteroid = client

    @listener
    async def on_message_create(self, message: Message):
        ...

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
