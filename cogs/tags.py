import asyncio

from discord import Embed, Message
from discord_slash import SlashContext, AutoCompleteContext, SlashCommandOptionType, Button, ButtonStyle, ComponentMessage, ComponentContext, Modal, ModalContext, TextInput, TextInputStyle
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice

from my_utils import (
    AsteroidBot,
    is_administrator_or_bot_owner,
    get_content,
    Cog,
    is_enabled,
)
from my_utils.errors import TagNotFound, NotTagOwner, TagsIsPrivate
from my_utils.models.guild_data import GuildTag


class Tags(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.name = "Tags"

    @Cog.listener(name="on_autocomplete")
    async def tag_autocomplete(self, ctx: AutoCompleteContext):
        if not self.bot.get_transformed_command_name(ctx).startswith("tag"):
            return
        if ctx.focused_option != "tag_name":
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
        name="open",
        description="Open tag",
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
    async def open_tag(self, ctx: SlashContext, tag_name: str):
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
            color=guild_data.configuration.language,
        )

        await ctx.send(embed=embed)

    @slash_subcommand(base="tag", name="add", description="Create new tag")
    @is_enabled()
    async def create_new_tag(self, ctx: SlashContext, tag_name: str, tag_content: str):
        tag_name = self.convert_tag_name(tag_name)

        await self._is_can_manage_tags(ctx)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        content = get_content("TAG_ADD_COMMAND", guild_data.configuration.language)

        tag = None
        for tag in guild_data.tags:
            if tag.name == tag_name:
                return await ctx.send(content["TAG_ALREADY_EXISTS_TEXT"], hidden=True)

        await guild_data.add_tag(
            tag_name,
            ctx.author_id,
            tag_content
        )
        await ctx.send(content=content["TAG_CREATED_TEXT"].format(tag_name=tag_name))

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

        content = get_content(
            "TAG_REMOVE_COMMAND", lang=guild_data.configuration.language
        )
        await ctx.send(content["TAG_REMOVED_TEXT"].format(tag_name=tag_name))

    @slash_subcommand(base="tag", name="list", description="Shows list of exists tags")
    @is_enabled()
    async def tag_list(self, ctx: SlashContext):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("FUNC_TAG_LIST", guild_data.configuration.language)

        description = ""
        for count, tag in enumerate(guild_data.tags, start=1):
            description += f'**{count}. {tag.name}**\n'
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
            content["TAG_RENAMED_TEXT"].format(
                tag_name=tag_name, new_tag_name=new_tag_name
            )
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
                    create_choice(
                        name="Moderators",
                        value="False"
                    ),
                    create_choice(
                        name="Everyone",
                        value="True"
                    )
                ]
            )
        ]
    )
    @is_enabled()
    @is_administrator_or_bot_owner()
    async def allow_public_tags(self, ctx: SlashContext, status: str):
        status = status == "True"
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.set_cog_data("Tags", {"is_public": status})

        content = get_content("PUBLIC_TAGS_COMMAND", guild_data.configuration.language)
        await ctx.send(content["TAGS_PUBLIC"] if status else content["TAGS_FOR_ADMINS"])

    @slash_subcommand(
        base="tag",
        name="embed",
        description="Open embed control tag menu",
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
    async def tag_embed(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("EMBED_TAG_CONTROL", guild_data.configuration.language)

        tag = None
        for tag in guild_data.tags:
            if tag.name == tag_name:
                break

        if tag and not tag.is_embed:
            return await ctx.send(content["NOT_SUPPORTED_TAG_TYPE"])

        await self._is_can_manage_tags(ctx, tag)

        if tag is None:
            embed, message = await self.init_btag(ctx, content)
            return await self._process_interactions(
                ctx, message, content, embed, tag_name
            )

        embed = Embed(
            title=tag.title,
            description=tag.description,
            color=guild_data.configuration.embed_color,
        )
        components = [
            [
                Button(
                    style=ButtonStyle.green,
                    label=content["EDIT_TAG_BUTTON"],
                    id="edit_tag",
                ),
                Button(
                    style=ButtonStyle.red,
                    label=content["REMOVE_TAG_BUTTON"],
                    id="remove_tag",
                ),
                Button(style=ButtonStyle.red, label=content["EXIT_BUTTON"], id="exit"),
            ]
        ]
        message: ComponentMessage = await ctx.send(embed=embed, components=components)

        await self._process_interactions(
            ctx, message, content, embed, tag_name
        )

    async def _process_interactions(
        self,
        ctx: SlashContext,
        message: ComponentMessage,
        content: dict,
        embed: Embed,
        tag_name: str,
    ):
        while True:
            try:
                button_ctx: ComponentContext = await self.bot.wait_for(
                    "button_click",
                    check=lambda inter: inter.author_id == ctx.author_id
                    and message.id == inter.origin_message.id,
                    timeout=600,
                )
            except asyncio.TimeoutError:
                return await message.delete()
            except Exception as e:
                continue

            button_id = button_ctx.custom_id

            if button_id == "edit_tag":
                await self.init_btag(ctx, content, message)
            elif button_id == "remove_tag":
                await self.remove_tag(content, button_ctx, tag_name)
                return await message.delete(delay=5)
            elif button_id == "exit":
                return await message.delete()
            elif button_id == "change_content":
                embed = await self.edit_tag(
                    ctx, button_ctx, embed, message, content
                )
            elif button_id == "save_tag":
                await self.save_tag(content, button_ctx, tag_name, embed)
            elif button_id == "get_raw":
                await self.get_raw_description(button_ctx, embed)

            if not button_ctx.responded:
                await button_ctx.defer(edit_origin=True)

    async def init_btag(
        self, ctx: SlashContext, content: dict, message: ComponentMessage = None
    ):
        components = [
            [
                Button(
                    style=ButtonStyle.blue,
                    label=content["CHANGE_CONTENT_BUTTON"],
                    id="change_content",
                ),
                Button(
                    style=ButtonStyle.gray,
                    label=content["GET_RAW_DESCRIPTION_BUTTON"],
                    id="get_raw",
                ),
                Button(
                    style=ButtonStyle.green,
                    label=content["SAVE_TAG_BUTTON"],
                    id="save_tag",
                ),
                Button(style=ButtonStyle.red, label=content["EXIT_BUTTON"], id="exit"),
            ]
        ]

        if message is not None:
            return await message.edit(components=components)

        embed = Embed(
            title=content["TAG_TITLE_TEXT"],
            description=content["TAG_DESCRIPTION_TEXT"],
            color=await self.bot.get_embed_color(ctx.guild_id),
        )
        message: ComponentMessage = await ctx.send(embed=embed, components=components)
        return embed, message

    async def edit_tag(
        self,
        ctx: SlashContext,
        button_ctx: ComponentContext,
        embed: Embed,
        message: ComponentMessage,
        content: dict,
    ):
        modal = Modal(
            custom_id="change_embed_content",
            title=content["MODAL_TITLE"],
            components=[
                TextInput(
                    label=content["MODAL_SET_TITLE"],
                    custom_id="embed_title",
                    style=TextInputStyle.SHORT,
                    value=embed.title,
                    placeholder=content["MODAL_TITLE_PLACEHOLDER"],
                    max_length=32
                ),
                TextInput(
                    label=content["MODAL_SET_DESCRIPTION"],
                    custom_id="embed_description",
                    style=TextInputStyle.PARAGRAPH,
                    value=embed.description,
                    placeholder=content["MODAL_DESCRIPTION_PLACEHOLDER"]
                )
            ]
        )
        await button_ctx.popup(modal)
        modal_ctx: ModalContext = await self.bot.wait_for(
            "modal",
            check=lambda _modal_ctx: _modal_ctx.author_id == ctx.author_id and _modal_ctx.custom_id == "change_embed_content"
        )
        embed.title = modal_ctx.values["embed_title"]
        embed.description = modal_ctx.values["embed_description"]
        await modal_ctx.send(content["SUCCESSFULLY"], hidden=True)
        await message.edit(embed=embed)
        return embed

    async def save_tag(
        self, content: dict, ctx: ComponentContext, tag_name: str, embed: Embed
    ):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.add_tag(
            name=tag_name,
            author_id=ctx.author_id,
            description=embed.description,
            is_embed=True,
            title=embed.title
        )

        await ctx.send(content["SAVED_TAG_TEXT"], hidden=True)

    async def get_raw_description(self, ctx: ComponentContext, embed: Embed):
        tag_description = embed.description
        await ctx.send(content=f"```{tag_description}```", hidden=True)

    async def remove_tag(
        self,
        content: dict,
        ctx: ComponentContext,
        tag_name: str,
    ):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.remove_tag(tag_name)
        await ctx.send(content=content["REMOVED_TAG_TEXT"], hidden=True)

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
