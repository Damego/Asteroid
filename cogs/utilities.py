import datetime
from typing import List

from discord import (
    Embed,
    TextChannel,
    RawReactionActionEvent,
    Guild,
    Message,
    Member,
    Role,
)
from discord_slash import SlashContext, AutoCompleteContext, SlashCommandOptionType
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from pymongo.collection import Collection

from my_utils import (
    AsteroidBot,
    Cog,
    bot_owner_or_permissions,
    get_content,
    is_enabled,
    consts,
    NoData,
)


class Utilities(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = "🧰"
        self.name = "Utilities"

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        ...

    # STARBOARD

    @Cog.listener("on_autocomplete")
    async def starboard_autocomplete(self, ctx: AutoCompleteContext, **kwargs):
        if ctx.name != "starboard":
            return

        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if not starboard_data:
            return
        if starboard_data.get("blacklist") is None:
            return
        blacklist_data = starboard_data["blacklist"]

        if ctx.focused_option == "channel":
            channel_ids = blacklist_data.get("channels")
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
            member_ids = blacklist_data.get("members")
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
            role_ids = blacklist_data.get("roles")
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

        collection = self.bot.get_guild_main_collection(payload.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if starboard_data is None:
            return
        if not starboard_data["is_enabled"]:
            return
        if payload.channel_id == starboard_data["channel_id"]:
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
        limit = starboard_data["limit"]
        if stars_count < limit:
            return

        starboard_channel: TextChannel = guild.get_channel(starboard_data["channel_id"])
        exists_messages = starboard_data.get("messages")
        if exists_messages is None or str(payload.message_id) not in exists_messages:
            await self._send_starboard_message(
                collection, message, stars_count, starboard_channel
            )
        else:
            starboard_message_id = starboard_data["messages"][str(payload.message_id)][
                "starboard_message"
            ]
            await self._update_starboard_message(
                starboard_channel, starboard_message_id, stars_count
            )

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return

        collection = self.bot.get_guild_main_collection(payload.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if starboard_data is None:
            return
        if not starboard_data["is_enabled"]:
            return
        if payload.channel_id == starboard_data["channel_id"]:
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

        starboard_channel: TextChannel = guild.get_channel(starboard_data["channel_id"])
        starboard_message_id = starboard_data["messages"][str(payload.message_id)][
            "starboard_message"
        ]
        await self._update_starboard_message(
            starboard_channel, starboard_message_id, stars_count
        )

    @staticmethod
    def _is_blacklisted(
        payload: RawReactionActionEvent, message: Message, starboard_data: dict
    ):
        blacklist = starboard_data.get("blacklist")
        if not blacklist:
            return False
        blacklisted_channels = blacklist.get("channels")
        blacklisted_roles = blacklist.get("roles")
        blacklisted_members = blacklist.get("members")
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
        collection: Collection,
        message: Message,
        stars_count: int,
        starboard_channel: TextChannel,
    ):
        lang = self.bot.get_guild_bot_lang(message.guild.id)
        content = get_content("STARBOARD_FUNCTIONS", lang)
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

        collection.update_one(
            {"_id": "starboard"},
            {
                "$set": {
                    f"messages.{message.id}.starboard_message": starboard_message.id
                }
            },
        )

    @slash_subcommand(
        base="starboard", name="channel", description="Starboard channel setting"
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_channel(self, ctx: SlashContext, channel: TextChannel):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", lang)

        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if starboard_data is None:
            data = {"is_enabled": True, "channel_id": channel.id, "limit": 3}
        else:
            data = {"channel_id": channel.id}
        collection.update_one({"_id": "starboard"}, {"$set": data}, upsert=True)
        await ctx.send(content["CHANNEL_WAS_SETUP_TEXT"])

    @slash_subcommand(base="starboard", name="limit", description="Limit setting")
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_stars_limit(self, ctx: SlashContext, limit: int):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", lang)

        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        collection.update_one(
            {"_id": "starboard"}, {"$set": {"limit": limit}}, upsert=True
        )
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
                    create_choice(name="enable", value="enable"),
                    create_choice(name="disable", value="disable"),
                ],
            )
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def set_starboard_status(self, ctx: SlashContext, status: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", lang)

        _status = status == "enable"
        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if (
            starboard_data is None
            or "channel_id" not in starboard_data
            or "limit" not in starboard_data
        ):
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"])

        collection.update_one(
            {"_id": "starboard"}, {"$set": {"is_enabled": _status}}, upsert=True
        )
        if _status:
            message_content = content["STARBOARD_ENABLED_TEXT"]
        else:
            message_content = content["STARBOARD_DISABLED_TEXT"]

        await ctx.send(message_content)

    @slash_subcommand(
        base="starboard",
        subcommand_group="blacklist",
        name="add",
        description="Adds a member, role or channel in blacklist",
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
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", lang)

        if not member and not role and not channel:
            return await ctx.send(content["BLACKLIST_NO_OPTIONS_TEXT"], hidden=True)

        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if starboard_data is None:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)

        data = {}
        if "blacklist" not in starboard_data:
            if member:
                data["members"] = member.id
            if role:
                data["roles"] = role.id
            if channel:
                data["channels"] = channel.id
        else:
            blacklist = starboard_data["blacklist"]
            if member and member.id not in blacklist["members"]:
                data["members"] = member.id
            if role and role.id not in blacklist["roles"]:
                data["roles"] = role.id
            if channel and channel.id not in blacklist["channels"]:
                data["channels"] = channel.id

        to_send = {f"blacklist.{key}": value for key, value in data.items()}

        collection.update_one({"_id": "starboard"}, {"$push": to_send}, upsert=True)

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
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", lang)

        if not member and not role and not channel:
            return await ctx.send(content["BLACKLIST_NO_OPTIONS_TEXT"])

        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if starboard_data is None:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)

        data = {}
        if "blacklist" not in starboard_data:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)

        blacklist = starboard_data["blacklist"]
        if member:
            member = ctx.guild.get_member(int(member))
            if member.id in blacklist["members"]:
                data["members"] = member.id
        if role:
            role = ctx.guild.get_role(int(role))
            if role.id in blacklist["roles"]:
                data["roles"] = role.id
        if channel:
            channel = ctx.guild.get_channel(int(channel))
            if channel.id in blacklist["channels"]:
                data["channels"] = channel.id

        to_send = {f"blacklist.{key}": value for key, value in data.items()}

        collection.update_one({"_id": "starboard"}, {"$pull": to_send}, upsert=True)

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
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("STARBOARD_FUNCTIONS", lang)

        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        starboard_data = collection.find_one({"_id": "starboard"})
        if starboard_data is None:
            return await ctx.send(content["STARBOARD_NOT_SETUP_TEXT"], hidden=True)
        if "blacklist" not in starboard_data or not starboard_data["blacklist"]:
            return await ctx.send(content["EMPTY_BLACKLIST_TEXT"], hidden=True)

        embed = Embed(
            title=content["BLACKLIST_TEXT"],
            color=self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.datetime.now(),
        )
        members = starboard_data["blacklist"].get("members")
        channels = starboard_data["blacklist"].get("channels")
        roles = starboard_data["blacklist"].get("roles")

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
    async def command_autocomplete(self, ctx: AutoCompleteContext, **kwargs):
        if self.bot.get_transformed_command_name(ctx) != "command":
            return
        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        configuration_data = collection.find_one({"_id": "configuration"})
        disabled_commands = configuration_data.get("disabled_commands")
        if disabled_commands:
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
        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        content = get_content(
            "COMMAND_CONTROL", lang=self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        collection.update_one(
            {"_id": "configuration"},
            {"$push": {"disabled_commands": command_name}},
            upsert=True,
        )

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
        collection = self.bot.get_guild_main_collection(ctx.guild_id)
        content = get_content(
            "COMMAND_CONTROL", lang=self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        collection.update_one(
            {"_id": "configuration"},
            {"$pull": {"disabled_commands": command_name}},
            upsert=True,
        )
        await ctx.send(content["COMMAND_ENABLED"].format(command_name=command_name))

    @slash_subcommand(
        base="todo",
        name="new",
        description="Adds a new todo in your todo's",
        guild_ids=consts.test_guild_id,
    )
    async def add_todo(self, ctx: SlashContext, todo_content: str):
        content = get_content(
            "TODO_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )
        message = await ctx.send(
            content["TODO_CREATED_TEXT"].format(todo_content=todo_content)
        )

        data = {
            "created_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "created_at_timestamp": datetime.datetime.now().timestamp(),
            "jump_url": message.jump_url,
            "message_id": message.id,
            "content": todo_content,
        }
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        collection.update_one(
            {"_id": str(ctx.author_id)}, {"$push": {"todo_list": data}}, upsert=True
        )

    @Cog.listener(name="on_autocomplete")
    async def todo_autocomplete(self, ctx: AutoCompleteContext):
        if not self.bot.get_transformed_command_name(ctx).startswith("todo"):
            return
        if ctx.focused_option == "todo":
            collection = self.bot.get_guild_users_collection(ctx.guild_id)
            user_data = collection.find_one({"_id": str(ctx.author_id)})
            if user_data is None:
                return
            user_todo_list = user_data.get("todo_list")
            if user_todo_list is None:
                return
            choices = [
                create_choice(
                    name=f"{count}. | {todo['created_at']} | {todo['content'][:10]}...",
                    value=todo["created_at"],
                )
                for count, todo in enumerate(user_todo_list, start=1)
                if ctx.user_input
                in f"{count}. {todo['created_at']} | {todo['content'][::10]}..."
            ][:25]
            await ctx.populate(choices)

    @slash_subcommand(
        base="todo",
        name="delete",
        description="Deletes a todo from your todo's",
        options=[
            create_option(
                name="todo",
                description="Your todo",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
        guild_ids=consts.test_guild_id,
    )
    async def delete_todo(self, ctx: SlashContext, todo: str):
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        user_data = collection.find_one({"_id": str(ctx.author_id)})
        if user_data is None:
            raise NoData
        user_todo_list = user_data.get("todo_list")
        if user_todo_list is None:
            raise NoData
        for todo_data in user_todo_list:
            if todo_data["created_at"] == todo:
                data = todo_data
                break
        else:
            raise NoData
        content = get_content(
            "TODO_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )
        await ctx.send(content["TODO_DELETED"])

        collection.update_one(
            {"_id": str(ctx.author_id)}, {"$pull": {"todo_list": data}}, upsert=True
        )

    @slash_subcommand(
        base="todo",
        name="list",
        description="Show your todo list",
        guild_ids=consts.test_guild_id,
    )
    async def todo_list(self, ctx: SlashContext):
        await ctx.defer()
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        user_data = collection.find_one({"_id": str(ctx.author_id)})
        if user_data is None:
            raise NoData
        user_todo_list = user_data.get("todo_list")
        if user_todo_list is None:
            raise NoData

        content = get_content(
            "TODO_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )
        embed = Embed(
            title=content["USER_TODO_LIST"].format(ctx.author.display_name),
            description="",
            color=self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        for count, todo_data in enumerate(user_todo_list, start=1):
            embed.add_field(
                name=f"{count}. *(<t:{int(todo_data['created_at_timestamp'])}:R>)*",
                value=f" ```{todo_data['content']}```",
                inline=False,
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utilities(bot))
