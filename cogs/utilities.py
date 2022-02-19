import datetime
from typing import List

from discord import (
    ChannelType,
    Embed,
    TextChannel,
    RawReactionActionEvent,
    Guild,
    Message,
    Member,
    Role,
    Forbidden,
)
from discord_slash import SlashContext, AutoCompleteContext, SlashCommandOptionType
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice

from my_utils import (
    AsteroidBot,
    Cog,
    bot_owner_or_permissions,
    get_content,
    is_enabled,
    consts,
    NoData,
)
from my_utils.models.guild_data import GuildData, GuildStarboard


class Utilities(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = "🧰"
        self.name = "Utilities"

    # STARBOARD

    @Cog.listener("on_autocomplete")
    async def starboard_autocomplete(self, ctx: AutoCompleteContext):
        if ctx.name != "starboard":
            return

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        starboard_data = guild_data.starboard
        if not starboard_data:
            return
        if starboard_data.blacklist is None:
            return

        if ctx.focused_option == "channel":
            channel_ids = starboard_data.blacklist.get("channels")
            if not channel_ids:
                return
            channels: List[TextChannel] = [
                ctx.guild.get_channel(channel_id) for channel_id in channel_ids
            ]
            choices = [
                create_choice(name=channel.name, value=str(channel.id))
                for channel in channels
                if channel.name.startswith(ctx.user_input)
            ][:25]
        elif ctx.focused_option == "member":
            member_ids = starboard_data.blacklist.get("members")
            if not member_ids:
                return
            members: List[Member] = [
                ctx.guild.get_member(member_id) for member_id in member_ids
            ]
            choices = [
                create_choice(name=member.display_name, value=str(member.id))
                for member in members
                if member.display_name.startswith(ctx.user_input)
            ][:25]
        elif ctx.focused_option == "role":
            role_ids = starboard_data.blacklist.get("roles")
            if not role_ids:
                return
            roles: List[Role] = [ctx.guild.get_role(role_id) for role_id in role_ids]
            choices = [
                create_choice(name=role.name, value=str(role.id))
                for role in roles
                if role.name.startswith(ctx.user_input)
            ][:25]

        await ctx.populate(choices)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return
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
        if stars_count < starboard_data.limit:
            return

        starboard_channel: TextChannel = guild.get_channel(starboard_data.channel_id)
        exists_messages = starboard_data.messages
        if exists_messages is None or str(payload.message_id) not in exists_messages:
            await self._send_starboard_message(
                guild_data, message, stars_count, starboard_channel
            )
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
        starboard_message_id = starboard_data.messages[str(payload.message_id)][
            "starboard_message"
        ]
        await self._update_starboard_message(
            starboard_channel, starboard_message_id, stars_count
        )

    @staticmethod
    def _is_blacklisted(
        payload: RawReactionActionEvent,
        message: Message,
        starboard_data: GuildStarboard,
    ):
        if not starboard_data.blacklist:
            return False
        blacklisted_channels = starboard_data.blacklist.get("channels", [])
        blacklisted_roles = starboard_data.blacklist.get("roles", [])
        blacklisted_members = starboard_data.blacklist.get("members", [])
        member_roles = message.guild.get_member(payload.user_id).roles
        has_blacklisted_roles = [
            role for role in member_roles if role.id in blacklisted_roles
        ]
        message_author_has_blacklisted_roles = [
            role for role in message.author.roles if role.id in blacklisted_roles
        ]

        if (
            blacklisted_channels
            and payload.channel_id in blacklisted_channels
            or blacklisted_members
            and (
                payload.user_id in blacklisted_members
                or message.author.id in blacklisted_members
            )
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
        embed_description = (
            f"{message.content}\n\n"
            f"**[{content['JUMP_TO_ORIGINAL_MESSAGE_TEXT']}]({message.jump_url})**"
        )
        embed = Embed(
            description=embed_description,
            color=0xEEE2A0,
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        starboard_message = await starboard_channel.send(
            content=f"⭐{stars_count} | {message.channel.mention}", embed=embed
        )

        await guild_data.starboard.add_starboard_message(
            message.id, starboard_message.id
        )

    @slash_subcommand(
        base="starboard",
        name="channel",
        description="Starboard channel setting",
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
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_channel(self, ctx: SlashContext, channel: TextChannel):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        try:
            await channel.send("Test message to check permission. You can delete this.")
        except Forbidden:
            return await ctx.send(
                f"Bot doesn't have permission to send messages in {channel.mention}"
            )

        if guild_data.starboard is None:
            await guild_data.add_starboard(
                channel_id=channel.id, limit=3, is_enabled=True
            )
        else:
            await guild_data.starboard.set_channel_id(channel.id)

        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)
        await ctx.send(content["CHANNEL_WAS_SETUP_TEXT"])

    @slash_subcommand(base="starboard", name="limit", description="Limit setting")
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_stars_limit(self, ctx: SlashContext, limit: int):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if not guild_data.starboard:
            await guild_data.add_starboard(limit=limit)
        else:
            await guild_data.starboard.set_limit(limit)

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
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_status(self, ctx: SlashContext, status: str):
        status = status == "True"
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        starboard_data = guild_data.starboard
        if (
            starboard_data is None
            or not starboard_data.channel_id
            or not starboard_data.limit
        ):
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"])
        await starboard_data.set_status(status)

        await ctx.send(
            content["STARBOARD_ENABLED_TEXT"]
            if status
            else content["STARBOARD_DISABLED_TEXT"]
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
    @bot_owner_or_permissions(manage_guild=True)
    async def starboard_blacklist_add(
        self,
        ctx: SlashContext,
        member: Member = None,
        role: Role = None,
        channel: TextChannel = None,
    ):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        if not member and not role and not channel:
            return await ctx.send(content["BLACKLIST_NO_OPTIONS_TEXT"], hidden=True)

        starboard_data = guild_data.starboard
        if starboard_data is None:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)

        blacklist = starboard_data.blacklist
        if member and member.id not in blacklist.get("members", []):
            await starboard_data.add_member_to_blacklist(member.id)
        if role and role.id not in blacklist.get("roles", []):
            await starboard_data.add_role_to_blacklist(role.id)
        if channel and channel.id not in blacklist.get("channels", []):
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
    @bot_owner_or_permissions(manage_guild=True)
    async def starboard_blacklist_remove(
        self,
        ctx: SlashContext,
        member: str = None,
        role: str = None,
        channel: str = None,
    ):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        if not member and not role and not channel:
            return await ctx.send(content["BLACKLIST_NO_OPTIONS_TEXT"])

        starboard_data = guild_data.starboard
        if starboard_data is None:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)
        if not starboard_data.blacklist:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)

        blacklist = starboard_data.blacklist
        if member and int(member) in blacklist["members"]:
            await starboard_data.remove_member_from_blacklist(int(member))
        if role and int(role) in blacklist["roles"]:
            await starboard_data.remove_role_from_blacklist(int(role))
        if channel and int(channel) in blacklist["channels"]:
            await starboard_data.remove_channel_from_blacklist(int(channel))

        await ctx.send(content["BLACKLIST_REMOVED_TEXT"], hidden=True)

    @slash_subcommand(
        base="starboard",
        subcommand_group="blacklist",
        name="list",
        description="Shows starboard blacklist",
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def starboard_blacklist_list(self, ctx: SlashContext, hidden: bool = False):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", guild_data.configuration.language)

        starboard_data = guild_data.starboard
        if starboard_data is None:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)
        if not starboard_data.blacklist:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)

        embed = Embed(
            title=content["BLACKLIST_TEXT"],
            color=guild_data.configuration.embed_color,
            timestamp=datetime.datetime.now(),
        )
        members = starboard_data.blacklist.get("members")
        channels = starboard_data.blacklist.get("channels")
        roles = starboard_data.blacklist.get("roles")

        if not members and not channels and not roles:
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

    #  TURN OFF/ON COMMANDS/GROUP OF COMMANDS

    @Cog.listener(name="on_autocomplete")
    async def command_autocomplete(self, ctx: AutoCompleteContext):
        if self.bot.get_transformed_command_name(ctx) != "command":
            return

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        disabled_commands = guild_data.configuration.disabled_commands

        choices = [
            create_choice(name=command_name, value=command_name)
            for command_name in disabled_commands
            if command_name.startswith(ctx.user_input)
        ][:25]

        await ctx.populate(choices)

    @slash_subcommand(
        base="command",
        name="disable",
        description="Disable command/base/group for your server",
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def disable_cmd(self, ctx: SlashContext, command_name: str):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.configuration.add_disabled_command(command_name)

        content = get_content("COMMAND_CONTROL", lang=guild_data.configuration.language)
        await ctx.send(content["COMMAND_DISABLED"].format(command_name=command_name))

    @slash_subcommand(
        base="command",
        name="enable",
        description="Enable command/base/group for your server",
        options=[
            create_option(
                name="command_name",
                description="The name of command",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @bot_owner_or_permissions(manage_guild=True)
    async def enable_cmd(self, ctx: SlashContext, command_name: str):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.configuration.delete_disabled_command(command_name)

        content = get_content("COMMAND_CONTROL", lang=guild_data.configuration.language)
        await ctx.send(content["COMMAND_ENABLED"].format(command_name=command_name))

    @slash_subcommand(base="note", name="new", description="Create a note")
    @is_enabled()
    async def add_todo(self, ctx: SlashContext, name: str, note_content: str):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        embed = Embed(
            title=content["NOTE_CREATED_TEXT"].format(name=name),
            description=note_content,
        )
        message = await ctx.send(embed=embed)

        data = {
            "name": name,
            "created_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "created_at_timestamp": datetime.datetime.now().timestamp(),
            "jump_url": message.jump_url,
            "content": note_content,
        }
        user_data = await guild_data.get_user(ctx.author_id)
        await user_data.add_note(data)

    @Cog.listener(name="on_autocomplete")
    async def note_autocomplete(self, ctx: AutoCompleteContext):
        if not self.bot.get_transformed_command_name(ctx).startswith("note"):
            return
        if ctx.focused_option != "name":
            return

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(ctx.author_id)
        if not user_data.notes:
            return

        choices = [
            create_choice(
                name=f"{count}. | {note['created_at']} | {note['name']}",
                value=note["name"],
            )
            for count, note in enumerate(user_data.notes, start=1)
            if ctx.user_input in f"{count}. {note['created_at']} | {note['name']}"
        ][:25]

        await ctx.populate(choices)

    @slash_subcommand(
        base="note",
        name="delete",
        description="Delete a note",
        options=[
            create_option(
                name="name",
                description="The name of note",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def delete_note(self, ctx: SlashContext, name: str):
        await ctx.defer()
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(ctx.author_id)
        if not user_data.notes:
            raise NoData

        await user_data.remove_note(name)
        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        await ctx.send(content["NOTE_DELETED"])

    @slash_subcommand(base="note", name="list", description="Show your notes")
    @is_enabled()
    async def notes_list(self, ctx: SlashContext):
        await ctx.defer()
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(ctx.author_id)
        if not user_data.notes:
            raise NoData

        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        embed = Embed(
            title=content["USER_NOTE_LIST"].format(ctx.author.display_name),
            description="",
            color=guild_data.configuration.embed_color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        for count, todo_data in enumerate(user_data.notes, start=1):
            embed.add_field(
                name=f"{count}. *(<t:{int(todo_data['created_at_timestamp'])}:R>)*",
                value=f" ```{todo_data['content']}``` [{content['JUMP_TO']}]({todo_data['jump_url']})",
                inline=False,
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utilities(bot))
