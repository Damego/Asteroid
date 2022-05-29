import datetime
import re

from discord import Embed
from discord_slash import (
    AutoCompleteContext,
    Modal,
    ModalContext,
    SlashCommandOptionType,
    SlashContext,
    TextInput,
    TextInputStyle,
)
from discord_slash.cog_ext import cog_slash as slash_command
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import (
    AsteroidBot,
    Cog,
    DiscordColors,
    NoData,
    SystemChannels,
    bot_owner_or_permissions,
    consts,
    get_content,
    is_enabled,
    locales,
)

regex = re.compile(r"^#[a-fA-F0-9_-]{6}$")


class Utilities(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = "🧰"
        self.name = "Utilities"

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
        base_dm_permission=False,
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

    @slash_subcommand(
        base="note",
        name="new",
        description="Create a note",
        base_dm_permission=False,
    )
    @is_enabled()
    async def create_note(self, ctx: SlashContext, is_global: bool = False):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        modal = Modal(
            custom_id=f"create_note_modal|{'global' if is_global else 'guild'}",
            title=content["CREATE_NOTE_TITLE"],
            components=[
                TextInput(
                    style=TextInputStyle.SHORT,
                    custom_id="note_name",
                    label=content["NOTE_NAME_LABEL"],
                ),
                TextInput(
                    style=TextInputStyle.PARAGRAPH,
                    custom_id="note_content",
                    label=content["NOTE_CONTENT_LABEL"],
                ),
            ],
        )
        await ctx.popup(modal)

    @Cog.listener(name="on_modal")
    async def on_note_modal(self, ctx: ModalContext):
        if not ctx.custom_id.startswith("create_note_modal"):
            return

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        embed = Embed(
            title=content["NOTE_CREATED_TEXT"].format(name=ctx.values["note_name"]),
            description=ctx.values["note_content"],
            color=guild_data.configuration.embed_color,
        )
        message = await ctx.send(embed=embed, hidden=True)

        data = {
            "name": ctx.values["note_name"],
            "created_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "created_at_timestamp": datetime.datetime.now().timestamp(),
            "jump_url": message.jump_url,
            "content": ctx.values["note_content"],
        }
        if ctx.custom_id.endswith("guild"):
            user_data = await guild_data.get_user(ctx.author_id)
        else:
            global_data = await self.bot.mongo.get_global_data()
            user_data = await global_data.get_user(ctx.author_id)
        await user_data.add_note(data)

    @Cog.listener(name="on_autocomplete")
    async def note_autocomplete(self, ctx: AutoCompleteContext):
        if not self.bot.get_transformed_command_name(ctx).startswith("note"):
            return
        if ctx.focused_option != "name":
            return

        global_data = await self.bot.mongo.get_global_data()
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_guild_data = await guild_data.get_user(ctx.author_id)
        user_global_data = await global_data.get_user(ctx.author_id)
        if not user_guild_data.notes and not user_global_data.notes:
            return

        choices = [
            create_choice(
                name=f"{count}. | {note['created_at']} | {note['name']}",
                value=note["name"],
            )
            for count, note in enumerate(user_guild_data.notes + user_global_data.notes, start=1)
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
        await ctx.defer(hidden=True)
        global_data = await self.bot.mongo.get_global_data()
        user_global_data = await global_data.get_user(ctx.author_id)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_guild_data = await guild_data.get_user(ctx.author_id)
        if not user_guild_data.notes and not user_global_data.notes:
            raise NoData

        if name in [note["name"] for note in user_guild_data.notes]:
            await user_guild_data.remove_note(name)
        elif name in [note["name"] for note in user_global_data.notes]:
            await user_global_data.remove_note(name)
        else:
            raise NoData

        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        await ctx.send(content["NOTE_DELETED"], hidden=True)

    @slash_subcommand(base="note", name="list", description="Show your notes")
    @is_enabled()
    async def notes_list(self, ctx: SlashContext, hidden: bool = False):
        await ctx.defer(hidden=hidden)
        global_data = await self.bot.mongo.get_global_data()
        user_global_data = await global_data.get_user(ctx.author_id)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_guild_data = await guild_data.get_user(ctx.author_id)
        if not user_guild_data.notes and not user_global_data.notes:
            raise NoData

        content = get_content("NOTES_COMMANDS", guild_data.configuration.language)
        embed = Embed(
            title=content["USER_NOTE_LIST"].format(ctx.author.display_name),
            description="",
            color=guild_data.configuration.embed_color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        for count, note in enumerate(user_guild_data.notes + user_global_data.notes, start=1):
            embed.add_field(
                name=f"{count}. *(<t:{int(note['created_at_timestamp'])}:R>)*",
                value=f" ```{note['content']}``` [{content['JUMP_TO']}]({note['jump_url']})",
                inline=False,
            )

        await ctx.send(embed=embed, hidden=hidden)

    @slash_subcommand(
        base="global",
        name="music_playlist",
        description="Makes your playlist global. You can listen it everywhere.",
        options=[
            create_option(
                name="playlist",
                description="Your playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
        base_dm_permission=False,
    )
    async def global_music_playlist(self, ctx: SlashContext, playlist: str):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(ctx.author_id)
        if playlist not in user_data.music_playlists:
            raise NoData
        playlist_data = user_data.music_playlists[playlist]
        global_data = await self.bot.mongo.get_global_data()
        global_user = await global_data.get_user(ctx.author_id)
        await global_user.add_many_tracks(f"{playlist} — GLOBAL", playlist_data)

        await ctx.send("Now your playlist is global!", hidden=True)

    @slash_command(
        name="language",
        description="Changes bot's language on your server.",
        options=[
            create_option(
                name="language",
                description="Language",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                choices=[
                    create_choice(name=locale, value=locale) for locale in locales.locales_list
                ],
            )
        ],
        dm_permission=False,
    )
    @bot_owner_or_permissions(manage_roles=True)
    async def set_bot_language(self, ctx: SlashContext, language: str):
        await ctx.defer()
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.configuration.set_language(language)
        content = get_content("SET_LANGUAGE_COMMAND", lang=guild_data.configuration.language)
        await ctx.send(content["LANGUAGE_CHANGED"])

    @slash_command(
        name="embed_color",
        description="Set color for embeds",
        dm_permission=False,
    )
    @bot_owner_or_permissions(manage_roles=True)
    async def set_embed_color(self, ctx: SlashContext, color: str):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("SET_EMBED_COLOR_COMMAND", guild_data.configuration.language)
        if not regex.fullmatch(color):
            return await ctx.send(content["WRONG_COLOR"])
        color = f"0x{color.replace('#', '')}"

        await guild_data.configuration.set_embed_color(color)
        embed = Embed(title=content["SUCCESSFULLY_CHANGED"], color=int(color, 16))
        await ctx.send(embed=embed, delete_after=10)

    @slash_command(
        name="issue",
        description="Sends a issue to owner",
        dm_permission=False,
    )
    async def open_modal_bug(self, ctx: SlashContext):
        modal = Modal(
            custom_id="issue_modal",
            title="Issue menu",
            components=[
                TextInput(
                    style=TextInputStyle.SHORT,
                    custom_id="issue_name",
                    label="Title of the bug",
                    placeholder="[BUG] Command `info` doesn't work!",
                ),
                TextInput(
                    style=TextInputStyle.PARAGRAPH,
                    custom_id="issue_description",
                    label="Description",
                    placeholder="I found a interesting bug!",
                ),
            ],
        )
        await ctx.popup(modal)

    @Cog.listener(name="on_modal")
    async def on_issue_modal(self, ctx: ModalContext):
        if ctx.custom_id != "issue_modal":
            return

        await ctx.defer(hidden=True)

        issue_name = ctx.values["issue_name"]
        issue_description = ctx.values["issue_description"]

        embed = Embed(
            title=issue_name,
            description=issue_description,
            color=DiscordColors.RED,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        channel = self.bot.get_channel(SystemChannels.ISSUES_REPORT_CHANNEL)
        await channel.send(embed=embed)

        await ctx.send("Your issue was send to developer!", hidden=True)
        # TODO: Translate command

    @slash_subcommand(
        base="plugin",
        name="disable",
        description="Disables plugin on your server",
        options=[
            create_option(
                name="plugin",
                description="The name of plugin",
                option_type=SlashCommandOptionType.STRING,
                choices=[
                    create_choice(name=extension, value=extension)
                    for extension in consts.PUBLIC_EXTENSIONS
                ],
            )
        ],
        base_dm_permission=False,
    )
    async def plugin_disable(self, ctx: SlashContext, plugin: str):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.set_cog_data(plugin, {"disabled": True})
        await ctx.send(f"Plugin `{plugin}` disabled!", hidden=True)
        # TODO: Translate command

    @slash_subcommand(
        base="plugin",
        name="enable",
        description="Enables plugin on your server",
        options=[
            create_option(
                name="plugin",
                description="The name of plugin",
                option_type=SlashCommandOptionType.STRING,
                choices=[
                    create_choice(name=extension, value=extension)
                    for extension in consts.PUBLIC_EXTENSIONS
                ],
            )
        ],
    )
    async def plugin_enable(self, ctx: SlashContext, plugin: str):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.set_cog_data(plugin, {"disabled": False})
        await ctx.send(f"Plugin `{plugin}` enabled!", hidden=True)
        # TODO: Translate command


def setup(bot):
    bot.add_cog(Utilities(bot))
