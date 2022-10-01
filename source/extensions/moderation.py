from datetime import datetime

from interactions import MISSING, Color, CommandContext, Embed, Extension, Member, Message, option

from core import Asteroid, command, Mention, TimestampMention  # isort: skip


# TODO:
#   1. Warn system (warn limit before banning)
#   2. Locale
#   3. UI/UX


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
    @option("The member to ban")
    @option("The reason of banning")
    async def ban(self, ctx: CommandContext, member: Member, reason: str = None):
        """Bans a member"""
        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id:
            return await ctx.send(locale.CANNOT_BAN_BOT, ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_BAN_YOURSELF, ephemeral=True)

        await member.ban(ctx.guild_id, reason)

        await ctx.send(locale.MEMBER_BANNED(member=member))

    @mod_member.subcommand()
    @option("The member to kick")
    @option("The reason of kicking")
    async def kick(self, ctx: CommandContext, member: Member, reason: str = None):
        """Kicks a member"""
        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id:
            return await ctx.send(locale.CANNOT_KICK_BOT, ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_KICK_YOURSELF, ephemeral=True)

        await member.ban(ctx.guild_id, reason)

        await ctx.send(locale.MEMBER_KICKED(member=member))

    @mod_member.subcommand()
    @option("The member to warn")
    @option("The reason of warning")
    async def warn(self, ctx: CommandContext, member: Member, reason: str = None):
        """Warns a member"""
        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id or member.user.bot:
            return await ctx.send(locale.CANNOT_WARN_BOT, ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_WARN_YOURSELF, ephemeral=True)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        user_data = guild_data.get_user(int(member.id))

        if user_data is None:
            user_data = await guild_data.add_user(int(member.id))

        user_data.add_warn(author_id=int(ctx.author.id), warned_at=datetime.utcnow(), reason=reason)
        await user_data.update()

        await ctx.send(locale.MEMBER_WARNED)

    @mod_member.subcommand()
    @option("The member to view warns")
    async def warns(self, ctx: CommandContext, member: Member):
        """List of member warns"""
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        user_data = guild_data.get_user(int(member.id))
        locale = await self.client.get_locale(ctx.guild_id)

        if user_data is None or not user_data.warns:
            return await ctx.send(locale.NO_WARNS, ephemeral=True)

        embed = Embed(title=locale.WARNS_LIST, description="", color=Color.blurple())
        embed.set_thumbnail(url=member.user.avatar_url)
        embed.set_author(
            name=f"{member.user.username}#{member.user.discriminator}",
            icon_url=member.user.avatar_url,
        )

        for count, warn in enumerate(user_data.warns, start=1):
            embed.description += (
                f"**` {count} `**\n"
                f"> **{locale.AUTHOR}:** {Mention.USER.format(id=warn.author_id)}\n"
                f"> **{locale.WARNED_AT}:** {TimestampMention.LONG_DATE.format(int(warn.warned_at.timestamp()))}\n"
                + (f"> **{locale.REASON}:** {warn.reason}\n\n" if warn.reason else "\n\n")
            )

        await ctx.send(embeds=embed)

    @mod.group(name="channel")
    async def mod_channel(self, ctx: CommandContext):
        """Group command for channels"""

    @mod_channel.subcommand()
    @option("The amount of messages to delete", min_value=1, max_value=1000)
    @option("The member to delete messages for")
    @option("Whether to bulk delete the messages or to delete every message separately")
    async def purge(
        self, ctx: CommandContext, amount: int, member: Member = None, bulk: bool = True
    ):
        """Deletes the messages in the current channel"""

        def check(message: Message):
            return message.author.id == member.id

        await ctx.defer(ephemeral=True)

        channel = ctx.channel
        if channel is MISSING:
            channel = await self.client.get_channel(ctx.channel_id)

        _check = check if member is not None else MISSING

        await channel.purge(amount, check=_check, bulk=bulk)


def setup(client: Asteroid):
    Moderation(client)
