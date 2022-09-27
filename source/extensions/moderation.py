from interactions import (
    Channel,
    CommandContext,
    Extension,
    Member,
)
# from interactions import option

from core import Asteroid, BotException, MissingPermissions, GuildVoiceLobbies, command, listener  # isort: skip


class Moderation(Extension):
    def __init__(self, client) -> None:
        self.client: Asteroid = client

    @command()
    async def mod(self, ctx: CommandContext):
        """Base moderation command"""

    @mod.group(name="member")
    async def mod_member(self, ctx: CommandContext):
        """Group command for member"""

    @mod_member.subcommand()
    async def ban(self, ctx: CommandContext, member: Member):
        """Bans a member"""

    @mod_member.subcommand()
    async def kick(self, ctx: CommandContext, member: Member):
        """Kicks a member"""

    @mod_member.subcommand()
    async def warn(self, ctx: CommandContext, member: Member):
        """Warns a member"""

    @mod_member.subcommand()
    async def warns(self, ctx: CommandContext, member: Member):
        """List of member warns"""

    @mod.group(name="channel")
    async def mod_channel(self, ctx: CommandContext):
        """Group command for channels"""

    @mod_channel.subcommand()
    async def clear(self, ctx: CommandContext):
        """Clears the messages in the current channel"""

    