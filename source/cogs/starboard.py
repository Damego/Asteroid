import datetime

from discord import (
    ChannelType,
    Embed,
    Forbidden,
    Guild,
    Member,
    Message,
    RawReactionActionEvent,
    Role,
    TextChannel,
)
from discord_slash import AutoCompleteContext, Permissions, SlashCommandOptionType, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import AsteroidBot, Cog, GuildData, GuildStarboard, get_content, is_enabled


class StarBoard(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.name = "StarBoard"
        self.emoji = "⭐"

    @Cog.listener("on_autocomplete")
    async def starboard_autocomplete(self, ctx: AutoCompleteContext):
        if ctx.name != "starboard":
            return

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        starboard_data = guild_data.starboard
        if starboard_data.blacklist is None:
            return await ctx.populate([])

        if ctx.focused_option == "channel":
            choices = [
                create_choice(name=channel.name, value=str(channel.id))
                for channel in [
                    ctx.guild.get_channel(channel_id)
                    for channel_id in starboard_data.blacklist.channels
                ]
                if channel.name.startswith(ctx.user_input)
            ][:25]
        elif ctx.focused_option == "member":
            choices = [
                create_choice(name=member.display_name, value=str(member.id))
                for member in [
                    ctx.guild.get_member(member_id)
                    for member_id in starboard_data.blacklist.members
                ]
                if member.display_name.startswith(ctx.user_input)
            ][:25]
        elif ctx.focused_option == "role":
            choices = [
                create_choice(name=role.name, value=str(role.id))
                for role in [
                    ctx.guild.get_role(role_id) for role_id in starboard_data.blacklist.roles
                ]
                if role.name.startswith(ctx.user_input)
            ][:25]

        await ctx.populate(choices)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
        if str(payload.emoji) != "⭐":
            return

        guild_data = await self.bot.get_guild_data(payload.guild_id)
        starboard_data = guild_data.starboard
        if not starboard_data.is_enabled:
            return
        if payload.channel_id == starboard_data.channel_id:
            return

        guild: Guild = self.bot.get_guild(payload.guild_id)
        channel: TextChannel = guild.get_channel(payload.channel_id)
        message: Message = await channel.fetch_message(payload.message_id)
        if self._is_blacklisted(payload, message, starboard_data):
            return

        stars_count = 0
        for reaction in message.reactions:
            emoji = reaction.emoji
            if emoji == "⭐":
                stars_count = reaction.count
        if stars_count < starboard_data.limit:
            return

        starboard_channel: TextChannel = guild.get_channel(starboard_data.channel_id)
        exists_messages = starboard_data.messages
        if exists_messages is None or str(payload.message_id) not in exists_messages:
            await self._send_starboard_message(guild_data, message, stars_count, starboard_channel)
        else:
            starboard_message_id = starboard_data.messages[str(payload.message_id)][
                "starboard_message"
            ]
            await self._update_starboard_message(
                starboard_channel, starboard_message_id, stars_count
            )

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return

        guild_data = await self.bot.mongo.get_guild_data(payload.guild_id)
        starboard_data = guild_data.starboard
        if starboard_data is None:
            return
        if not starboard_data.is_enabled:
            return
        if payload.channel_id == starboard_data.channel_id:
            return

        guild: Guild = self.bot.get_guild(payload.guild_id)
        channel: TextChannel = guild.get_channel(payload.channel_id)
        message: Message = await channel.fetch_message(payload.message_id)

        if self._is_blacklisted(payload, message, starboard_data):
            return

        stars_count = 0
        for reaction in message.reactions:
            emoji = reaction.emoji
            if emoji == "⭐":
                stars_count = reaction.count

        starboard_channel: TextChannel = guild.get_channel(starboard_data.channel_id)
        starboard_message_id = starboard_data.messages[str(payload.message_id)]["starboard_message"]
        await self._update_starboard_message(starboard_channel, starboard_message_id, stars_count)

    @staticmethod
    def _is_blacklisted(
        payload: RawReactionActionEvent,
        message: Message,
        starboard_data: GuildStarboard,
    ):
        if not starboard_data.blacklist:
            return False
        blacklisted_channels = starboard_data.blacklist.channels
        blacklisted_roles = starboard_data.blacklist.roles
        blacklisted_members = starboard_data.blacklist.members
        member_roles = message.guild.get_member(payload.user_id).roles
        has_blacklisted_roles = [role for role in member_roles if role.id in blacklisted_roles]
        message_author_has_blacklisted_roles = [
            role for role in message.author.roles if role.id in blacklisted_roles
        ]

        if (
            blacklisted_channels
            and payload.channel_id in blacklisted_channels
            or blacklisted_members
            and (payload.user_id in blacklisted_members or message.author.id in blacklisted_members)
            or has_blacklisted_roles
            or message_author_has_blacklisted_roles
        ):
            return True

    @staticmethod
    async def _update_starboard_message(
        starboard_channel: TextChannel, starboard_message_id: int, stars_count: int
    ):
        starboard_message = await starboard_channel.fetch_message(starboard_message_id)
        origin_channel_mention = starboard_message.content.split()[2]
        message_content = f"⭐{stars_count} | {origin_channel_mention}"
        await starboard_message.edit(content=message_content)

    async def _send_starboard_message(
        self,
        guild_data: GuildData,
        message: Message,
        stars_count: int,
        starboard_channel: TextChannel,
    ):
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)
        jump_to = f"\n\n**[{content['JUMP_TO_ORIGINAL_MESSAGE_TEXT']}]({message.jump_url})**"
        if message.embeds:
            embed: Embed = message.embeds[0]
            embed.color = 0xEEE2A0
            embed.timestamp = datetime.datetime.now()
            embed.description = f"{embed.description}{jump_to}" if embed.description else jump_to
        else:
            embed = Embed(
                description=f"{message.content}{jump_to}",
                color=0xEEE2A0,
                timestamp=datetime.datetime.now(),
            )
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        starboard_message = await starboard_channel.send(
            content=f"⭐{stars_count} | {message.channel.mention}", embed=embed
        )

        await guild_data.starboard.add_starboard_message(message.id, starboard_message.id)

    @slash_subcommand(
        base="starboard",
        name="channel",
        description="Sets channel for starboard",
        base_dm_permission=False,
        base_default_member_permissions=Permissions.MANAGE_GUILD,
        options=[
            create_option(
                name="channel",
                description="Text channel",
                option_type=SlashCommandOptionType.CHANNEL,
                required=True,
                channel_types=[ChannelType.text],
            )
        ],
    )
    @is_enabled()
    async def starboard_channel(self, ctx: SlashContext, channel: TextChannel):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)

        try:
            await channel.send("Test message to check permission.", delete_after=5)
        except Forbidden:
            return await ctx.send(
                f"Bot doesn't have permission to send messages in {channel.mention}"
            )

        await guild_data.starboard.modify(channel_id=channel.id)

        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)
        await ctx.send(content["CHANNEL_WAS_SETUP_TEXT"])

    @slash_subcommand(
        base="starboard",
        name="limit",
        description="Limit setting",
        options=[
            create_option(
                name="limit",
                description="The limit of stars",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
                min_value=1,
                max_value=99,
            )
        ],
    )
    @is_enabled()
    async def starboard_limit(self, ctx: SlashContext, limit: int):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        await guild_data.starboard.modify(limit=limit)

        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)
        await ctx.send(content["LIMIT_WAS_SETUP_TEXT"].format(limit=limit))

    @slash_subcommand(
        base="starboard",
        name="status",
        description="Enable/disable starboard",
        options=[
            create_option(
                name="status",
                description="enable or disable starboard",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                choices=[
                    create_choice(name="Enable", value="True"),
                    create_choice(name="Disable", value="False"),
                ],
            )
        ],
    )
    @is_enabled()
    async def starboard_status(self, ctx: SlashContext, status: str):
        status = status == "True"
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        starboard_data = guild_data.starboard
        if not starboard_data.is_ready:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"])
        await starboard_data.modify(is_enabled=status)

        await ctx.send(
            content["STARBOARD_ENABLED_TEXT"] if status else content["STARBOARD_DISABLED_TEXT"]
        )

    @slash_subcommand(
        base="starboard",
        subcommand_group="blacklist",
        name="add",
        description="Adds a member, role or channel in blacklist",
        options=[
            create_option(
                name="member",
                description="member",
                option_type=SlashCommandOptionType.USER,
                required=False,
            ),
            create_option(
                name="role",
                description="Role",
                option_type=SlashCommandOptionType.ROLE,
                required=False,
            ),
            create_option(
                name="channel",
                description="Text channel",
                option_type=SlashCommandOptionType.CHANNEL,
                required=False,
                channel_types=[ChannelType.text],
            ),
        ],
    )
    @is_enabled()
    async def starboard_blacklist_add(
        self,
        ctx: SlashContext,
        member: Member = None,
        role: Role = None,
        channel: TextChannel = None,
    ):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        if not member and not role and not channel:
            return await ctx.send(content["BLACKLIST_NO_OPTIONS_TEXT"], hidden=True)

        starboard_data = guild_data.starboard
        if not starboard_data.is_ready:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)

        blacklist = starboard_data.blacklist
        if member and member.id not in blacklist.members:
            await starboard_data.add_member_to_blacklist(member.id)
        if role and role.id not in blacklist.roles:
            await starboard_data.add_role_to_blacklist(role.id)
        if channel and channel.id not in blacklist.channels:
            await starboard_data.add_channel_to_blacklist(channel.id)

        await ctx.send(content["BLACKLIST_ADDED_TEXT"], hidden=True)

    @slash_subcommand(
        base="starboard",
        subcommand_group="blacklist",
        name="remove",
        description="Removes member/role/channel from blacklist",
        options=[
            create_option(
                name="member",
                description="member",
                option_type=SlashCommandOptionType.STRING,
                required=False,
                autocomplete=True,
            ),
            create_option(
                name="role",
                description="Role",
                option_type=SlashCommandOptionType.STRING,
                required=False,
                autocomplete=True,
            ),
            create_option(
                name="channel",
                description="Text channel",
                option_type=SlashCommandOptionType.STRING,
                required=False,
                autocomplete=True,
            ),
        ],
    )
    @is_enabled()
    async def starboard_blacklist_remove(
        self,
        ctx: SlashContext,
        member: str = None,
        role: str = None,
        channel: str = None,
    ):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        if not member and not role and not channel:
            return await ctx.send(content["BLACKLIST_NO_OPTIONS_TEXT"])

        starboard_data = guild_data.starboard
        if not starboard_data.is_ready:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)
        if starboard_data.blacklist.is_empty:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)

        blacklist = starboard_data.blacklist
        if member and int(member) in blacklist.members:
            await starboard_data.remove_member_from_blacklist(int(member))
        if role and int(role) in blacklist.roles:
            await starboard_data.remove_role_from_blacklist(int(role))
        if channel and int(channel) in blacklist.channels:
            await starboard_data.remove_channel_from_blacklist(int(channel))

        await ctx.send(content["BLACKLIST_REMOVED_TEXT"], hidden=True)

    @slash_subcommand(
        base="starboard",
        subcommand_group="blacklist",
        name="view",
        description="Shows starboard blacklist",
    )
    @is_enabled()
    async def starboard_blacklist_view(self, ctx: SlashContext, hidden: bool = False):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        starboard_data = guild_data.starboard
        if not starboard_data.is_ready:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)
        blacklist = starboard_data.blacklist
        if blacklist.is_empty:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)

        embed = Embed(
            title=content["BLACKLIST_TEXT"],
            color=guild_data.configuration.embed_color,
            timestamp=datetime.datetime.now(),
        )
        members = starboard_data.blacklist.members
        channels = starboard_data.blacklist.channels
        roles = starboard_data.blacklist.roles

        if starboard_data.blacklist.is_empty:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)
        if members:
            embed.add_field(
                name=content["MEMBERS"],
                value=", ".join([f"<@{user_id}>" for user_id in members]),
                inline=False,
            )
        if channels:
            embed.add_field(
                name=content["CHANNELS"],
                value=", ".join([f"<#{channel_id}>" for channel_id in channels]),
                inline=False,
            )
        if roles:
            embed.add_field(
                name=content["ROLES"],
                value=", ".join([f"<@&{role_id}>" for role_id in roles]),
                inline=False,
            )

        await ctx.send(embed=embed, hidden=hidden)


def setup(bot):
    bot.add_cog(StarBoard(bot))
