from datetime import datetime

from discord import Embed
from discord_slash import (
    AutoCompleteContext,
    Modal,
    ModalContext,
    Permissions,
    SlashCommandOptionType,
    SlashContext,
    TextInput,
    TextInputStyle,
)
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import AsteroidBot, Cog, GuildTag, get_content, is_administrator_or_bot_owner, is_enabled
from utils.errors import NotTagOwner, TagNotFound, TagsIsPrivate


class Tags(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.name = "Tags"
        self.emoji = "🏷️"

    @Cog.listener(name="on_autocomplete")
    async def tag_autocomplete(self, ctx: AutoCompleteContext):
        if ctx.name != "tag" or ctx.focused_option != "name":
            return
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        choices = [
            create_choice(name=tag.name, value=tag.name)
            for tag in guild_data.tags
            if ctx.user_input in tag.name
        ][:25]
        await ctx.populate(choices)

    @slash_subcommand(
        base="tag",
        name="view",
        description="View an existing tag",
        base_dm_permission=False,
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def tag_view(self, ctx: SlashContext, name: str):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        tag = guild_data.get_tag(name)
        if tag is None:
            raise TagNotFound
        if not tag.is_embed:
            return await ctx.send(tag.description)

        embed = Embed(
            title=tag.title,
            description=tag.description,
            color=guild_data.configuration.embed_color,
        )

        await ctx.send(embed=embed)

        await tag.modify(uses_count=tag.uses_count + 1)

    @slash_subcommand(
        base="tag",
        name="create",
        description="Create new tag",
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            ),
            create_option(
                name="type",
                description="The type of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                choices=[
                    create_choice(name="Simple", value="Simple"),
                    create_choice(name="Embed", value="Embed"),
                ],
            ),
        ],
    )
    @is_enabled()
    async def tag_create(self, ctx: SlashContext, name: str, type: str):
        await self._is_can_manage_tags(ctx)
        guild_data = await self.bot.get_guild_data(ctx.guild_id)

        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        tag = guild_data.get_tag(name)
        if tag is not None:
            return await ctx.send(content["TAG_ALREADY_EXISTS_TEXT"], hidden=True)

        if type == "Embed":
            modal = Modal(
                custom_id=f"modal_new_tag|embed|{name}",
                title=content["MODAL_TITLE"],
                components=[
                    TextInput(
                        label=content["MODAL_SET_TITLE"],
                        custom_id="title",
                        style=TextInputStyle.SHORT,
                        placeholder=content["MODAL_TITLE_PLACEHOLDER"],
                        max_length=32,
                    ),
                    TextInput(
                        label=content["MODAL_SET_DESCRIPTION"],
                        custom_id="description",
                        style=TextInputStyle.PARAGRAPH,
                        placeholder=content["MODAL_DESCRIPTION_PLACEHOLDER"],
                    ),
                ],
            )
        elif type == "Normal":
            modal = Modal(
                custom_id=f"modal_new_tag|normal|{name}",
                title=content["MODAL_TITLE"],
                components=[
                    TextInput(
                        label=content["MODAL_SET_DESCRIPTION"],
                        custom_id="description",
                        style=TextInputStyle.PARAGRAPH,
                        placeholder=content["MODAL_DESCRIPTION_PLACEHOLDER"],
                    )
                ],
            )
        await ctx.popup(modal)

    @slash_subcommand(
        base="tag",
        name="edit",
        description="Edit a current tag",
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def tag_edit(self, ctx: SlashContext, name: str):
        await self._is_can_manage_tags(ctx)
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        tag = guild_data.get_tag(name)
        if tag is None:
            raise TagNotFound

        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        if tag.is_embed:
            modal = Modal(
                custom_id=f"modal_edit_tag|embed|{name}",
                title=content["MODAL_TITLE"],
                components=[
                    TextInput(
                        label=content["MODAL_SET_TITLE"],
                        custom_id="title",
                        style=TextInputStyle.SHORT,
                        placeholder=content["MODAL_TITLE_PLACEHOLDER"],
                        max_length=32,
                        value=tag.title,
                    ),
                    TextInput(
                        label=content["MODAL_SET_DESCRIPTION"],
                        custom_id="description",
                        style=TextInputStyle.PARAGRAPH,
                        placeholder=content["MODAL_DESCRIPTION_PLACEHOLDER"],
                        value=tag.description,
                    ),
                ],
            )
        else:
            modal = Modal(
                custom_id=f"modal_edit_tag|normal|{name}",
                title=content["MODAL_TITLE"],
                components=[
                    TextInput(
                        label=content["MODAL_SET_DESCRIPTION"],
                        custom_id="description",
                        style=TextInputStyle.PARAGRAPH,
                        placeholder=content["MODAL_DESCRIPTION_PLACEHOLDER"],
                        value=tag.description,
                    )
                ],
            )

        await ctx.popup(modal)

    @Cog.listener()
    async def on_modal(self, ctx: ModalContext):
        if not any(_id in ctx.custom_id for _id in ["modal_new_tag", "modal_edit_tag"]):
            return

        custom_id, type, name = ctx.custom_id.split("|")
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        if custom_id == "modal_new_tag":
            await self._is_can_manage_tags(ctx)
            await guild_data.add_tag(
                name=name,
                author_id=ctx.author_id,
                title=ctx.values["title"] if type == "embed" else "No title",
                description=ctx.values["description"],
                is_embed=type == "embed",
                created_at=int(datetime.now().timestamp()),
            )
            await ctx.send(content["TAG_CREATED_TEXT"].format(tag_name=name), hidden=True)
        elif custom_id == "modal_edit_tag":
            tag = guild_data.get_tag(name)
            await tag.modify(
                title=ctx.values["title"] if type == "embed" else None,
                description=ctx.values["description"],
                last_edited_at=int(datetime.now().timestamp()),
            )
            await ctx.send(content["TAG_EDITED_TEXT"].format(tag_name=name), hidden=True)

    @slash_subcommand(
        base="tag",
        name="remove",
        description="Removes tag",
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def tag_remove(self, ctx: SlashContext, name: str):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        tag = guild_data.get_tag(name)

        if tag is None:
            raise TagNotFound
        await self._is_can_manage_tags(ctx, tag)
        await guild_data.remove_tag(name)

        content = get_content("TAG_REMOVE_COMMAND", lang=guild_data.configuration.language)
        await ctx.send(content["TAG_REMOVED_TEXT"].format(tag_name=name))

    @slash_subcommand(base="tag", name="list", description="Shows list of exists tags")
    @is_enabled()
    async def tag_list(self, ctx: SlashContext):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("FUNC_TAG_LIST", guild_data.configuration.language)

        description = ""
        for count, tag in enumerate(guild_data.tags, start=1):
            description += f"**{count}. {tag.name}**\n"
            count += 1
        if not description:
            description = content["NO_TAGS_TEXT"]

        embed = Embed(
            title=content["TAGS_LIST_TEXT"].format(server=ctx.guild.name),
            description=description,
            color=guild_data.configuration.embed_color,
        )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="tag",
        name="rename",
        description="Renames tag's name",
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="new_name",
                description="New name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            ),
        ],
    )
    @is_enabled()
    async def tag_rename(self, ctx: SlashContext, name: str, new_name: str):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("TAG_RENAME_TAG", guild_data.configuration.language)
        tag = guild_data.get_tag(name)

        if tag is None:
            raise TagNotFound

        await self._is_can_manage_tags(ctx, tag)

        await tag.modify(name=new_name)
        await ctx.send(content["TAG_RENAMED_TEXT"].format(tag_name=name, new_tag_name=new_name))

    @slash_subcommand(
        base="tag",
        name="raw",
        description="Show raw tag description",
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def tag_raw(self, ctx: SlashContext, name: str):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        tag = guild_data.get_tag(name)
        if tag is None:
            raise TagNotFound

        tag_content = tag.description.replace("`", "\`")  # noqa: W605
        await ctx.reply(f"```{tag_content}```")

    @slash_subcommand(
        base="tag",
        name="info",
        description="Show information about tag",
        options=[
            create_option(
                name="name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def tag_info(self, ctx: SlashContext, name: str):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        tag = guild_data.get_tag(name)
        if tag is None:
            raise TagNotFound

        embed = Embed(title=tag.name, color=guild_data.configuration.embed_color)
        embed.add_field(name="Author", value=f"<@{tag.author_id}>")
        embed.add_field(name="Created at", value=f"<t:{tag.created_at}:R>")
        if tag.last_edited_at is not None:
            embed.add_field(name="Last edited at", value=f"<t:{tag.last_edited_at}:R>")
        embed.add_field(name="Uses count", value=tag.uses_count)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="tags",
        name="set_control",
        description="Allows or disallows everyone to use tags",
        base_dm_permission=False,
        base_default_member_permissions=Permissions.ADMINISTRATOR,
        options=[
            create_option(
                name="status",
                description="Who can manage tags in your server",
                required=True,
                option_type=SlashCommandOptionType.STRING,
                choices=[
                    create_choice(name="Moderators", value="False"),
                    create_choice(name="Everyone", value="True"),
                ],
            )
        ],
    )
    @is_enabled()
    @is_administrator_or_bot_owner()
    async def tags_set__control(self, ctx: SlashContext, status: str):
        status = status == "True"
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        await guild_data.modify_cog("Tags", is_public=status)

        content = get_content("PUBLIC_TAGS_COMMAND", guild_data.configuration.language)
        await ctx.send(content["TAGS_PUBLIC"] if status else content["TAGS_FOR_ADMINS"])

    async def _is_can_manage_tags(self, ctx: SlashContext, tag: GuildTag = None):
        if ctx.author.guild_permissions.manage_guild:
            return
        if tag and tag.author_id != ctx.author_id:
            raise NotTagOwner

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        tags_data = guild_data.cogs_data.get("tags")
        if not tags_data or tags_data.get("is_public"):
            return
        if tags_data.get("is_public") is False:
            raise TagsIsPrivate


def setup(bot):
    bot.add_cog(Tags(bot))
