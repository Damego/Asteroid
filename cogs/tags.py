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
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option

from utils import AsteroidBot, Cog, GuildTag, get_content, is_administrator_or_bot_owner, is_enabled
from utils.errors import NotTagOwner, TagNotFound, TagsIsPrivate


class Tags(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.name = "Tags"

    @Cog.listener(name="on_autocomplete")
    async def tag_autocomplete(self, ctx: AutoCompleteContext):
        if ctx.name != "tag" and ctx.focused_option != "tag_name":
            return
        choices = None
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        tags = guild_data.tags
        if choices := [
            create_choice(name=tag.name, value=tag.name)
            for tag in tags
            if tag.name.startswith(ctx.user_input)
        ][:25]:
            await ctx.populate(choices)

    @slash_subcommand(
        base="tag",
        name="view",
        description="View an existing tag",
        options=[
            create_option(
                name="tag_name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def view_tag(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        tag = None
        for tag in guild_data.tags:
            if tag.name == tag_name:
                break
        if tag is None:
            raise TagNotFound
        if tag.is_embed is False:
            return await ctx.send(tag.description)

        embed = Embed(
            title=tag.title,
            description=tag.description,
            color=guild_data.configuration.embed_color,
        )

        await ctx.send(embed=embed)

    @slash_subcommand(
        base="tag",
        name="create",
        description="Create new tag",
        options=[
            create_option(
                name="tag_name",
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
                    create_choice(name="Normal", value="Normal"),
                    create_choice(name="Embed", value="Embed"),
                ],
            ),
        ],
    )
    @is_enabled()
    async def create_new_tag(self, ctx: SlashContext, tag_name: str, type: str):
        tag_name = self.convert_tag_name(tag_name)

        await self._is_can_manage_tags(ctx)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        tag = None
        for tag in guild_data.tags:
            if tag.name == tag_name:
                return await ctx.send(content["TAG_ALREADY_EXISTS_TEXT"], hidden=True)

        if type == "Embed":
            modal = Modal(
                custom_id=f"modal_new_tag|embed|{tag_name}",
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
                custom_id=f"modal_new_tag|normal|{tag_name}",
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
                name="tag_name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def edit_tag(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)

        await self._is_can_manage_tags(ctx)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        tag = None
        for tag in guild_data.tags:
            if tag.name == tag_name:
                break
        if tag is None:
            raise TagNotFound

        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        if tag.is_embed:
            modal = Modal(
                custom_id=f"modal_edit_tag|embed|{tag_name}",
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
                custom_id=f"modal_edit_tag|normal|{tag_name}",
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

        custom_id, type, tag_name = ctx.custom_id.split("|")
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        if custom_id == "modal_new_tag":
            await self._is_can_manage_tags(ctx)
            await guild_data.add_tag(
                name=tag_name,
                author_id=ctx.author_id,
                description=ctx.values["description"],
                is_embed=type == "embed",
                title=ctx.values["title"] if type == "embed" else "No title",
            )
            await ctx.send(content["TAG_CREATED_TEXT"].format(tag_name=tag_name), hidden=True)
        elif custom_id == "modal_edit_tag":
            tag = None
            for tag in guild_data.tags:
                if tag.name == tag_name:
                    break
            if type == "embed":
                await tag.set_title(ctx.values["title"])
            await tag.set_description(ctx.values["description"])
            await ctx.send(content["TAG_EDITED_TEXT"].format(tag_name=tag_name), hidden=True)

    @slash_subcommand(
        base="tag",
        name="remove",
        description="Removes tag",
        options=[
            create_option(
                name="tag_name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def tag_remove(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        for tag in guild_data.tags:
            if tag.name == tag_name:
                await guild_data.remove_tag(tag_name)
                break
        else:
            raise TagNotFound
        await self._is_can_manage_tags(ctx, tag)

        content = get_content("TAG_REMOVE_COMMAND", lang=guild_data.configuration.language)
        await ctx.send(content["TAG_REMOVED_TEXT"].format(tag_name=tag_name))

    @slash_subcommand(base="tag", name="list", description="Shows list of exists tags")
    @is_enabled()
    async def tag_list(self, ctx: SlashContext):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
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
                name="tag_name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="new_tag_name",
                description="New name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            ),
        ],
    )
    @is_enabled()
    async def rename(self, ctx: SlashContext, tag_name: str, new_tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        new_tag_name = self.convert_tag_name(new_tag_name)

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("TAG_RENAME_TAG", guild_data.configuration.language)

        for tag in guild_data.tags:
            if tag.name == tag_name:
                await guild_data.remove_tag(tag_name)
                break
        else:
            raise TagNotFound

        await self._is_can_manage_tags(ctx, tag)

        await tag.rename(new_tag_name)
        await ctx.send(
            content["TAG_RENAMED_TEXT"].format(tag_name=tag_name, new_tag_name=new_tag_name)
        )

    @slash_subcommand(
        base="tag",
        name="raw",
        description="Show raw tag description",
        options=[
            create_option(
                name="tag_name",
                description="The name of tag",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def raw(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        for tag in guild_data.tags:
            if tag.name == tag_name:
                await guild_data.remove_tag(tag_name)
                break
        else:
            raise TagNotFound

        await self._is_can_manage_tags(ctx, tag)

        tag_content = tag.description
        await ctx.reply(f"```{tag_content}```")

    @slash_subcommand(
        base="tags",
        name="set_control",
        description="Allows or disallows everyone to use tags",
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
    async def allow_public_tags(self, ctx: SlashContext, status: str):
        status = status == "True"
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.set_cog_data("Tags", {"is_public": status})

        content = get_content("PUBLIC_TAGS_COMMAND", guild_data.configuration.language)
        await ctx.send(content["TAGS_PUBLIC"] if status else content["TAGS_FOR_ADMINS"])

    async def _is_can_manage_tags(self, ctx: SlashContext, tag: GuildTag = None):
        if ctx.author.guild_permissions.manage_guild:
            return
        if tag and tag.author_id != ctx.author_id:
            raise NotTagOwner

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        tags_data = guild_data.cogs_data.get("tags")
        if not tags_data or tags_data.get("is_public"):
            return
        if tags_data.get("is_public") is False:
            raise TagsIsPrivate

    @staticmethod
    def convert_tag_name(tag_name: str):
        tag_name = tag_name.lower().strip()

        if " " in tag_name:
            tag_name = tag_name.replace(" ", "")
        if "-" in tag_name:
            tag_name = tag_name.replace("-", "")
        if "_" in tag_name:
            tag_name = tag_name.replace("_", "")

        return tag_name


def setup(bot):
    bot.add_cog(Tags(bot))
