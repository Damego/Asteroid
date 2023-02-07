from datetime import datetime

from interactions import Choice, EmbedField, Extension, Modal, TextInput, TextStyleType
from interactions import extension_modal as modal
from interactions import option
from rapidfuzz import fuzz, process

from core import Asteroid, BotException, Mention, TimestampMention, command, listener
from core.context import CommandContext
from core.database.models import GuildTag
from utils import create_embed


def build_modal(
    ctx: CommandContext,
    is_embed: bool = True,
    *,
    name: str = None,
    title: str = None,
    description: str = None,
    custom_id: str = None,
) -> Modal:
    components = [
        TextInput(
            label=ctx.translate("MODAL_TAG_NAME"),
            custom_id="name",
            placeholder="The cool tag",
            required=True,
            style=TextStyleType.SHORT,
            value=name,
        ),
        TextInput(
            label=ctx.translate("MODAL_TAG_CONTENT"),
            custom_id="content",
            placeholder="There is a way to apply for moderator",
            required=True,
            style=TextStyleType.PARAGRAPH,
            value=description,
        ),
    ]
    if is_embed:
        components.insert(
            1,
            TextInput(
                label=ctx.translate("MODAL_TAG_TITLE"),
                custom_id="title",
                placeholder="Apply for moderator",
                required=True,
                style=TextStyleType.SHORT,
                value=title,
            ),
        )

    return Modal(
        title=ctx.translate("MODAL_CREATE_TAG"),
        custom_id=custom_id or "modal_create_tag",
        components=components,
    )


class Tags(Extension):
    def __init__(self, client) -> None:
        self.client: Asteroid = client

    @command()
    async def tag(self, ctx: CommandContext):
        """Command for tags"""

    @staticmethod
    def _process_tag_name(tag: GuildTag):
        return tag.name.lower().strip()

    @tag.autocomplete("name")
    async def tag_autocomplete(self, ctx: CommandContext, user_input: str):
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        options = process.extract(
            user_input.lower(),
            guild_data.tags,
            scorer=fuzz.partial_ratio,
            processor=self._process_tag_name,
            limit=25,
            score_cutoff=75,
        )
        choices = [Choice(name=tag.name, value=tag.name) for tag, _, _ in options]
        await ctx.populate(choices)

    @tag.subcommand(name="view")
    @option(description="The name of tag to view", autocomplete=True)
    async def tag_view(self, ctx: CommandContext, name: str):
        """View a tag"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        tag = guild_data.get_tag(name)
        if tag is None:
            raise BotException("TAG_NOT_FOUND", name=name)

        if tag.is_embed:
            await ctx.send(embeds=create_embed(description=tag.description, title=tag.title))
        else:
            await ctx.send(tag.description)

        tag.uses_count += 1
        await tag.update()

    @tag.subcommand(name="create")
    @option(
        description="The type of tag",
        choices=[Choice(name=i, value=i.lower()) for i in {"Embed", "Simple"}],
    )
    async def tag_create(self, ctx: CommandContext, type: str):
        """Create a tag"""
        await ctx.popup(build_modal(ctx, type == "embed"))

    @modal("modal_create_tag")
    async def modal_create_tag(
        self, ctx: CommandContext, name: str, title: str, content: str = None
    ):
        await ctx.defer(ephemeral=True)

        if content is None:
            title, content = content, title

        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        await guild_data.add_tag(
            name=name,
            title=title,
            description=content,
            author_id=int(ctx.author.id),
            is_embed=title is not None,
            created_at=int(datetime.utcnow().timestamp()),
            last_edited_at=None,
            uses_count=0,
        )

        translate = ctx.translate("TAG_CREATED").format(tag_name=name)
        await ctx.send(embeds=create_embed(translate))

    @tag.subcommand(name="delete")
    @option(description="The name of tag to delete", autocomplete=True)
    async def tag_delete(self, ctx: CommandContext, name: str):
        """Delete a tag"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        await guild_data.remove_tag(name)

        translate = ctx.translate("TAG_CREATED").format(tag_name=name)
        await ctx.send(translate)

    @tag.subcommand(name="edit")
    @option(description="The name of tag to edit", autocomplete=True)
    async def tag_edit(self, ctx: CommandContext, name: str):
        """Edit a tag"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        tag = guild_data.get_tag(name)
        if tag is None:
            raise BotException("TAG_NOT_FOUND", name=name)

        await ctx.popup(
            build_modal(
                ctx,
                is_embed=tag.is_embed,
                name=tag.name,
                title=tag.title,
                description=tag.description,
                custom_id=f"modal_edit_tag|{tag.name}",  # We should store current name of tag because we can change it
            )
        )

    @listener
    async def on_modal(self, ctx: CommandContext):
        def get_value(ind: int):
            return ctx.data.components[ind].components[0].value

        if not ctx.data.custom_id.startswith("modal_edit_tag"):
            return

        await ctx.defer(ephemeral=True)
        name = get_value(0)
        if len(ctx.data.components) == 3:
            title = get_value(1)
            description = get_value(2)
        else:
            title = None
            description = get_value(1)

        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        tag = guild_data.get_tag(ctx.data.custom_id.split("|")[1])
        tag.name = name
        tag.title = title
        tag.description = description
        tag.last_edited_at = int(datetime.utcnow().timestamp())

        await tag.update()

        translate = ctx.translate("TAG_EDITED").format(tag_name=name)
        await ctx.send(translate)

    @tag.subcommand(name="list")
    async def tag_list(self, ctx: CommandContext):
        """Show list of tags"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        description = "\n".join(
            [f"**` {ind} `** `{tag.name}`" for ind, tag in enumerate(guild_data.tags, start=1)]
        )
        translate = ctx.translate("TAG_LIST")
        await ctx.send(embeds=create_embed(description=description, title=translate))

    @tag.subcommand(name="info")
    @option(description="The name of tag to view", autocomplete=True)
    async def tag_info(self, ctx: CommandContext, name: str):
        """Show information about tag"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        tag = guild_data.get_tag(name)
        if tag is None:
            raise BotException("TAG_NOT_FOUND", name=name)

        def get_timestamp_string(timestamp: int):
            return (
                f"{TimestampMention.LONG.format(timestamp)} "
                f"({TimestampMention.RELATIVE.format(timestamp)})"
            )

        translate = ctx.translate
        fields = [
            EmbedField(
                name=translate("AUTHOR"), value=Mention.USER.format(id=tag.author_id), inline=True
            ),
            EmbedField(name=translate("USES_COUNT"), value=f"`{tag.uses_count}`", inline=True),
            EmbedField(
                name=translate("TIMESTAMPS"),
                value=f"**{translate('CREATED_AT')}** {get_timestamp_string(tag.created_at)}\n"
                + (
                    f"**{translate('LAST_EDITED_AT')}** {get_timestamp_string(tag.last_edited_at)}"
                    if tag.last_edited_at is not None
                    else ""
                ),
                inline=True,
            ),
        ]
        embed = create_embed(title=tag.name, fields=fields)
        await ctx.send(embeds=embed)


def setup(client):
    Tags(client)
