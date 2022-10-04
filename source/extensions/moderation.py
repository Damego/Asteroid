from datetime import datetime

from interactions import (
    MISSING,
    Color,
    CommandContext,
    Embed,
    Extension,
    Member,
    Message,
    Permissions,
    SelectMenu,
    SelectOption,
    option,
)

from core import Asteroid, Mention, MissingPermissions, TimestampMention, command


class Moderation(Extension):
    def __init__(self, client) -> None:
        self.client: Asteroid = client

    @command()
    async def mod(self, ctx: CommandContext):
        """Base moderation command"""

    @mod.subcommand()
    @option(
        "The limit of warns before banning a member. Set to 0 to disable system",
        min_value=0,
        max_value=10,  # 10 is fine?
    )
    @option("The moderator role to use special commands")
    async def configure(self, ctx: CommandContext, warns_to_ban: int):
        """Configures warns and moderator role"""
        # TODO: Wait for interactions-checks
        if not ctx.has_permissions(Permissions.MANAGE_GUILD):
            raise MissingPermissions(Permissions.MANAGE_GUILD)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        guild_data.settings.warns_limit = warns_to_ban
        await guild_data.settings.update()

        locale = await self.client.get_locale(ctx.guild_id)
        await ctx.send(locale.SUCCESSFULLY_CONFIGURED)

    @mod.group(name="member")
    async def mod_member(self, ctx: CommandContext):
        """Group command for member"""

    @mod_member.subcommand()
    @option("The member to ban")
    @option("The reason of banning")
    async def ban(self, ctx: CommandContext, member: Member, reason: str = None):
        """Bans a member of the server"""
        if not ctx.has_permissions(Permissions.BAN_MEMBERS):
            raise MissingPermissions(Permissions.BAN_MEMBERS)

        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id:
            return await ctx.send(locale.CANNOT_BAN_BOT, ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_BAN_YOURSELF, ephemeral=True)

        await member.ban(ctx.guild_id, reason)

        await ctx.send(locale.MEMBER_BANNED(member=member), ephemeral=True)

    @mod_member.subcommand()
    @option("The member to kick")
    @option("The reason of kicking")
    async def kick(self, ctx: CommandContext, member: Member, reason: str = None):
        """Kicks a member of the server"""
        if not ctx.has_permissions(Permissions.KICK_MEMBERS):
            raise MissingPermissions(Permissions.KICK_MEMBERS)

        locale = await self.client.get_locale(ctx.guild_id)

        if member.id == self.client.me.id:
            return await ctx.send(locale.CANNOT_KICK_BOT, ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_KICK_YOURSELF, ephemeral=True)

        await member.ban(ctx.guild_id, reason)

        await ctx.send(locale.MEMBER_KICKED(member=member), ephemeral=True)

    @mod_member.subcommand()
    @option("The member to warn")
    @option("The reason of warning")
    async def warn(self, ctx: CommandContext, member: Member, reason: str = None):
        """Warns a member"""
        if not ctx.has_permissions(Permissions.MODERATE_MEMBERS):
            raise MissingPermissions(Permissions.MODERATE_MEMBERS)

        locale = await self.client.get_locale(ctx.guild_id)
        guild_data = await self.client.database.get_guild(ctx.guild_id)

        if not guild_data.settings.warns_limit:
            return await ctx.send(
                locale.WARN_SYSTEM_DISABLED, ephemeral=True
            )  # TODO: Make it for all systems

        if member.id == self.client.me.id or member.user.bot:
            return await ctx.send(locale.CANNOT_WARN_BOT, ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(locale.CANNOT_WARN_YOURSELF, ephemeral=True)

        user_data = guild_data.get_user(int(member.id))

        if user_data is None:
            user_data = await guild_data.add_user(int(member.id))

        user_data.add_warn(author_id=int(ctx.author.id), warned_at=datetime.utcnow(), reason=reason)
        await user_data.update()

        if len(user_data.warns) >= guild_data.settings.warns_limit:
            await member.ban(ctx.guild_id, reason="[AUTO] Exceeded limit of warns")
            return await ctx.send(locale.MEMBER_BANNED(member=member))

        await ctx.send(
            locale.MEMBER_WARNED(member=member, amount=len(user_data.warns)), ephemeral=True
        )

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
                + (f"> **{locale.REASON}:** {warn.reason}" if warn.reason else "")
                + "\n\n"
            )

        components = []
        if ctx.has_permissions(Permissions.MODERATE_MEMBERS):
            components = [
                SelectMenu(
                    placeholder=locale.REMOVE_WARNS,
                    custom_id="select_remove_user_warn",
                    options=[
                        SelectOption(name=i + 1, value=i) for i in range(len(user_data.warns))
                    ],
                )
            ]

        await ctx.send(embeds=embed, commponents=components)

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
        if not ctx.has_permissions(Permissions.MANAGE_CHANNELS):
            raise MissingPermissions(Permissions.MANAGE_CHANNELS)

        def check(message: Message):
            return message.author.id == member.id

        await ctx.defer(ephemeral=True)

        channel = ctx.channel
        if channel is MISSING:
            channel = await self.client.get_channel(ctx.channel_id)

        _check = check if member is not None else MISSING

        messages = await channel.purge(amount, check=_check, bulk=bulk)

        locale = await self.client.get_locale(ctx.guild_id)
        await ctx.send(locale.MESSAGES_REMOVED(amount=len(messages)))


def setup(client: Asteroid):
    Moderation(client)
