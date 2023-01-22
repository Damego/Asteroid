from datetime import datetime

from interactions import (
    Color,
    Embed,
    Extension,
    Member,
    Permissions,
    SelectMenu,
    SelectOption,
    option,
)

from core import (
    Asteroid,
    GuildUser,
    Mention,
    MissingPermissions,
    TimestampMention,
    command,
    listener,
)
from core.context import CommandContext, ComponentContext

# TODO:
#   Send embed messages


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
    async def configure(self, ctx: CommandContext, warns_to_ban: int):
        """Configures warns and moderator role"""
        if not ctx.has_permissions(Permissions.MODERATE_MEMBERS):
            raise MissingPermissions(Permissions.MODERATE_MEMBERS)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        guild_data.settings.warns_limit = warns_to_ban
        await guild_data.settings.update()

        translate = ctx.translate("SUCCESSFULLY_CONFIGURED")
        await ctx.send(translate)

    @mod.group(name="member")
    async def mod_member(self, ctx: CommandContext):
        """Group command for member"""

    @mod_member.subcommand()
    @option("The member to ban")
    @option("The reason of banning")
    async def ban(self, ctx: CommandContext, member: Member, reason: str = None):
        """Bans a member of the server"""
        if not await ctx.has_permissions(Permissions.BAN_MEMBERS):
            raise MissingPermissions(Permissions.BAN_MEMBERS)

        translate = ctx.translate

        if member.id == self.client.me.id:
            return await ctx.send(translate("CANNOT_BAN_BOT"), ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(translate("CANNOT_BAN_YOURSELF"), ephemeral=True)

        await member.ban(ctx.guild_id, reason=reason)

        await ctx.send(translate("MEMBER_BANNED", member=member), ephemeral=True)

    @mod_member.subcommand()
    @option("The member to kick")
    @option("The reason of kicking")
    async def kick(self, ctx: CommandContext, member: Member, reason: str = None):
        """Kicks a member of the server"""
        if not await ctx.has_permissions(Permissions.KICK_MEMBERS):
            raise MissingPermissions(Permissions.KICK_MEMBERS)

        translate = ctx.translate

        if member.id == self.client.me.id:
            return await ctx.send(translate("CANNOT_KICK_BOT"), ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(translate("CANNOT_KICK_YOURSELF"), ephemeral=True)

        await member.kick(ctx.guild_id, reason)

        await ctx.send(translate("MEMBER_KICKED", member=member), ephemeral=True)

    @mod_member.subcommand()
    @option("The member to warn")
    @option("The reason of warning")
    async def warn(self, ctx: CommandContext, member: Member, reason: str = None):
        """Warns a member"""
        if not await ctx.has_permissions(Permissions.MODERATE_MEMBERS):
            raise MissingPermissions(Permissions.MODERATE_MEMBERS)

        translate = ctx.translate
        guild_data = await self.client.database.get_guild(ctx.guild_id)

        if not guild_data.settings.warns_limit:
            return await ctx.send(
                translate("WARN_SYSTEM_DISABLED"), ephemeral=True
            )  # TODO: Make it for all systems

        if member.id == self.client.me.id or member.user.bot:
            return await ctx.send(translate("CANNOT_WARN_BOT"), ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(translate("CANNOT_WARN_YOURSELF"), ephemeral=True)

        user_data = guild_data.get_user(int(member.id))

        if user_data is None:
            user_data = await guild_data.add_user(int(member.id))

        user_data.add_warn(author_id=int(ctx.author.id), warned_at=datetime.utcnow(), reason=reason)
        await user_data.update()

        if len(user_data.warns) >= guild_data.settings.warns_limit:
            await member.ban(ctx.guild_id, reason="[AUTO] Exceeded limit of warns")
            return await ctx.send(translate("MEMBER_BANNED", member=member))

        await ctx.send(
            translate("MEMBER_WARNED", member=member, amount=len(user_data.warns)), ephemeral=True
        )

    @mod_member.subcommand()
    @option("The member to view warns")
    async def warns(self, ctx: CommandContext, member: Member):
        """List of member warns"""
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        user_data = guild_data.get_user(int(member.id))
        translate = ctx.translate

        if user_data is None or not user_data.warns:
            return await ctx.send(translate("NO_WARNS"), ephemeral=True)

        embed, components = await self._render_user_warns(ctx, member, user_data)
        await ctx.send(embeds=embed, components=components)

    @staticmethod
    async def _render_user_warns(
        ctx: CommandContext | ComponentContext,
        member: Member,
        user_data: GuildUser,
    ):
        embed = Embed(title=ctx.translate("WARNS_LIST"), description="", color=Color.BLURPLE)
        embed.set_thumbnail(url=member.user.avatar_url)
        embed.set_author(
            name=f"{member.user.username}#{member.user.discriminator}",
            icon_url=member.user.avatar_url,
        )

        for count, warn in enumerate(user_data.warns, start=1):
            embed.description += (
                f"**` {count} `**\n"
                f"> **{ctx.translate('AUTHOR')}:** {Mention.USER.format(id=warn.author_id)}\n"
                f"> **{ctx.translate('WARNED_AT')}:** {TimestampMention.LONG_DATE.format(int(warn.warned_at.timestamp()))}\n"
                + (f"> **{ctx.translate('REASON')}:** {warn.reason}" if warn.reason else "")
                + "\n"
            )

        components = []
        if await ctx.has_permissions(Permissions.MODERATE_MEMBERS):
            components = [
                SelectMenu(
                    placeholder=ctx.translate("SELECT_REMOVE_WARNS"),
                    custom_id=f"select_remove_user_warn|{member.id}",
                    options=[
                        SelectOption(label=i + 1, value=i) for i in range(len(user_data.warns))
                    ],
                    max_values=len(user_data.warns),
                )
            ]

        return embed, components

    @listener(name="on_component")
    async def select_remove_user_warns(self, ctx: ComponentContext):
        if not ctx.custom_id.startswith("select_remove_user_warn"):
            return
        if not await ctx.has_permissions(Permissions.MODERATE_MEMBERS):
            raise MissingPermissions(Permissions.MODERATE_MEMBERS)

        await ctx.defer(ephemeral=True)

        member_id = int(ctx.custom_id.split("|")[1])
        warn_indexes: list[int] = list(map(int, ctx.data.values))

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        user_data = guild_data.get_user(member_id)
        translate = ctx.translate

        # Does it work?
        warns = {i: warn for i, warn in enumerate(user_data.warns)}

        for index in warn_indexes:
            user_data.warns.remove(warns[index])

        await user_data.update()

        if user_data.warns:
            member = await self.client.get_member(ctx.guild_id, member_id)
            embed, components = await self._render_user_warns(ctx, member, user_data)
            await ctx.message.edit(embeds=embed, components=components)
        else:
            await ctx.message.delete("[AUTO-MOD] User don't have warns.")

        if len(warn_indexes) == 1:
            await ctx.send(translate("WARN_REMOVED"))
        else:
            await ctx.send(translate("WARNS_REMOVED"))

    @mod.group(name="channel")
    async def mod_channel(self, ctx: CommandContext):
        """Group command for channels"""

    # TODO: Restore after fix for Channel.purge
    # @mod_channel.subcommand()
    # @option("The amount of messages to delete", min_value=1, max_value=1000)
    # @option("The member to delete messages for")
    # @option("Whether to bulk delete the messages or to delete every message separately")
    # async def purge(
    #     self, ctx: CommandContext, amount: int, member: Member = None, bulk: bool = True
    # ):
    #     """Deletes the messages in the current channel"""
    #     if not await ctx.has_permissions(Permissions.MANAGE_CHANNELS):
    #         raise MissingPermissions(Permissions.MANAGE_CHANNELS)
    #
    #     def check(message: Message):
    #         return message.author.id == member.id
    #
    #     await ctx.defer(ephemeral=True)
    #
    #     channel = ctx.channel
    #     if channel is MISSING:
    #         channel = await self.client.get_channel(ctx.channel_id)
    #
    #     _check = check if member is not None else MISSING
    #
    #     messages = await channel.purge(amount, check=_check, bulk=bulk)
    #
    #     await ctx.send(ctx.translate("MESSAGES_REMOVED", amount=len(messages)))


def setup(client: Asteroid):
    Moderation(client)
