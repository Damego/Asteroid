from datetime import datetime

from interactions import CommandContext, Extension, Member, option

from core import Asteroid, GuildUser, command  # isort: skip


class Moderation(Extension):
    def __init__(self, client) -> None:
        self.client: Asteroid = client

    @command()
    async def mod(self, ctx: CommandContext):
        """Base moderation command"""
        await ctx.defer(ephemeral=True)

    @mod.group(name="member")
    async def mod_member(self, ctx: CommandContext):
        """Group command for member"""

    @mod_member.subcommand()
    @option("The member to ban")
    @option("The reason of banning")
    async def ban(self, ctx: CommandContext, member: Member, reason: str | None = None):
        """Bans a member"""
        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id:
            return await ctx.send(locale.CANNOT_BAN_BOT)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_BAN_YOURSELF)

        await member.ban(ctx.guild_id, reason)

        await ctx.send(locale.MEMBER_BANNED(member=member))

    @mod_member.subcommand()
    @option("The member to kick")
    @option("The reason of kicking")
    async def kick(self, ctx: CommandContext, member: Member, reason: str | None = None):
        """Kicks a member"""
        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id:
            return await ctx.send(locale.CANNOT_KICK_BOT)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_KICK_YOURSELF)

        await member.ban(ctx.guild_id, reason)

        await ctx.send(locale.MEMBER_KICKED(member=member))

    @mod_member.subcommand()
    @option("The member to warn")
    @option("The reason of warning")
    async def warn(self, ctx: CommandContext, member: Member, reason: str | None = None):
        """Warns a member"""
        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id or member.user.bot:
            return await ctx.send(locale.CANNOT_WARN_BOT)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_WARN_YOURSELF)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        user_data = await guild_data.get_user(int(member.id))

        user_data: GuildUser
        if user_data is None:
            user_data = await guild_data.add_user(int(member.id))

        user_data.add_warn(author_id=int(ctx.author.id), warned_at=datetime.utcnow(), reason=reason)
        await user_data.update()

        await ctx.send(locale.MEMBER_WARNED)

    @mod_member.subcommand()
    @option("The member to view warns")
    async def warns(self, ctx: CommandContext, member: Member):
        """List of member warns"""

    @mod.group(name="channel")
    async def mod_channel(self, ctx: CommandContext):
        """Group command for channels"""

    @mod_channel.subcommand()
    @option("The amount of messages to delete", min_value=1, max_value=1000)
    async def purge(self, ctx: CommandContext, amount: int):
        """Deletes the messages in the current channel"""
