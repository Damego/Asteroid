import datetime
import re
from asyncio import get_event_loop, sleep
from collections import defaultdict

from interactions import (
    Button,
    ButtonStyle,
    Channel,
    ChannelType,
    Choice,
    Color,
    CommandContext,
    Embed,
    Extension,
    LibraryException,
    Message,
    MessageReaction,
)
from interactions import extension_command as command
from interactions import extension_listener as listener
from interactions import option

from core import Asteroid, GuildEmojiBoard, GuildMessageData, Mention  # isort: skip

# TODO:
#   UI/UX
#   Exceptions
#   Locale


class EmojiBoards(Extension):
    def __init__(self, client):
        self.client: Asteroid = client

    @listener()
    async def on_message_reaction_add(self, reaction: MessageReaction):
        guild_data = await self.client.database.get_guild(int(reaction.guild_id))
        emoji = reaction.emoji
        for emoji_board in guild_data.emoji_boards:
            if emoji_board.emojis and str(emoji) in emoji_board.emojis:
                break
        else:
            return

        channel: Channel = await self.client.get(Channel, object_id=int(reaction.channel_id))
        message = await channel.get_message(reaction.message_id)
        if message.author.id == reaction.user_id:
            return await message.remove_reaction_from(emoji, reaction.user_id)
        if (
            int(reaction.channel_id) == emoji_board.channel_id
            and message.author.id == self.client.me.id
        ):
            return

        _message = emoji_board.get_message(message_id=int(reaction.message_id))
        if _message is None:
            _message = emoji_board.add_message(
                int(message.author.id), message_id=int(reaction.message_id)
            )

        _message.add_user(int(reaction.user_id))
        await emoji_board.update()

        count = len(_message.users)
        if count < emoji_board.to_add:
            return
        if count == emoji_board.to_add:
            return await self.__add_message(message, _message, emoji_board, count)

        await self.__update_message(_message, emoji_board, count)

    @listener()
    async def on_raw_message_reaction_remove(self, reaction: MessageReaction):
        guild_data = await self.client.database.get_guild(int(reaction.guild_id))
        emoji = reaction.emoji
        for emoji_board in guild_data.emoji_boards:
            if emoji_board.emojis and str(emoji) in emoji_board.emojis:
                break
        else:
            return

        _message = emoji_board.get_message(int(reaction.message_id))
        if _message is None:
            _message = emoji_board.add_message(message_id=int(reaction.message_id))

        _message.remove_user(int(reaction.user_id))
        await emoji_board.update()
        count = len(_message.users)

        if count > emoji_board.to_remove:
            return
        if count == emoji_board.to_remove:
            return await self.__remove_message(_message, emoji_board)

        await self.__update_message(_message, emoji_board, count)

    async def __add_message(
        self,
        message: Message,
        message_data: GuildMessageData,
        emoji_board: GuildEmojiBoard,
        count: int,
    ):
        if message.embeds:
            embed = message.embeds[0]
        else:
            embed = Embed(
                description=message.content,
                color=emoji_board.embed_color or Color.blurple(),
            )
        embed.timestamp = datetime.datetime.utcnow().isoformat()
        embed.set_author(name=message.author.username, icon_url=message.author.avatar_url)
        embed.set_footer(text=f"Emoji board name: {emoji_board.name}")

        view_msg_button = Button(style=ButtonStyle.LINK, label="Original message", url=message.url)

        channel: Channel = await self.client.get(Channel, object_id=emoji_board.channel_id)
        board_message = await channel.send(
            f"**{' '.join(emoji_board.emojis)} | {count}**",
            embeds=embed,
            components=view_msg_button,
        )
        message_data.channel_message_id = int(board_message.id)
        await emoji_board.update()

    async def __update_message(
        self, message_data: GuildMessageData, emoji_board: GuildEmojiBoard, count: int
    ):
        channel: Channel = await self.client.get(Channel, object_id=emoji_board.channel_id)
        board_message = await channel.get_message(message_data.channel_message_id)
        await board_message.edit(f"{emoji_board.emoji} | {count}")

    async def __remove_message(self, message_data: GuildMessageData, emoji_board: GuildEmojiBoard):
        channel: Channel = await self.client.get(Channel, object_id=emoji_board.channel_id)
        board_message = await channel.get_message(message_data.channel_message_id)
        await board_message.delete(
            "[EmojiBoard] Remove message because it lost all reaction that needed to be on board."
        )

        emoji_board.remove_message(message=message_data)
        await emoji_board.update()

    @listener()
    async def on_autocomplete(self, ctx: CommandContext):
        if ctx.data.name != "emoji_board":
            return

        focused_option = [_option for _option in ctx.data.options[0].options if _option.focused][0]
        if focused_option.name != "name":
            return
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        emoji_boards = guild_data.emoji_boards
        await ctx.populate(
            [Choice(name=emoji_board.name, value=emoji_board.name) for emoji_board in emoji_boards]
        )

    @command()
    async def emoji_board(self, ctx: CommandContext):
        ...

    @emoji_board.subcommand(name="create")
    @option("The name for your emoji board")
    @option("The text channel for sending messages", channel_types=[ChannelType.GUILD_TEXT])
    @option("The emoji for board")
    @option("Count to add emoji to board", min_value=1)
    @option("Count to remove emoji from board", min_value=0)
    @option("The HEX color for embeds without '#'", min_lenght=6, max_length=6)
    async def create_emoji_board(
        self,
        ctx: CommandContext,
        name: str,
        channel: Channel,
        emoji: str,
        to_add: int = 3,
        to_remove: int = 2,
        embed_color: str = None,
    ):
        """Create a new emoji board"""

        def remove_message(message: Message, timeout: int):
            async def inner():
                await sleep(timeout)
                await message.delete()

            loop = get_event_loop()
            loop.create_task(inner())

        await ctx.defer()

        if embed_color is not None and not re.fullmatch(r"[a-zA-z0-9]+", embed_color):
            raise Exception("Invalid color!")

        try:
            message = await channel.send("Test message to check bot permission")
        except LibraryException:
            return await ctx.send("Bot doesn't have permission to that channel!")

        remove_message(message, 5)

        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        if guild_data.emoji_boards:
            for _board in guild_data.emoji_boards:
                if emoji in _board.emojis:
                    raise  # Emoji taken

        await guild_data.add_emoji_board(
            name=name,
            channel_id=int(channel.id),
            emojis=[emoji],
            to_add=to_add,
            to_remove=to_remove,
            embed_color=int(embed_color, 16) if embed_color is not None else None,
        )

        await ctx.send("Emoji board created!")

    @emoji_board.subcommand(name="delete")
    @option("The name of emoji board to delete", autocomplete=True)
    async def delete_emoji_board(self, ctx: CommandContext, name: str):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        await guild_data.remove_emoji_board(name)
        await ctx.send("Emoji board deleted!")

    @emoji_board.subcommand(name="list")
    async def emoji_board_list(self, ctx: CommandContext):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        if not guild_data.emoji_boards:
            raise  # TODO: Exception

        embed = Embed(description="", title="Emoji boards")
        for emoji_board in guild_data.emoji_boards:
            embed.description += (
                f"**{emoji_board.name}** \n"
                f"> Emoji: {emoji_board.emoji} \n"
                f"> Messages: {len(emoji_board.messages)} \n\n"
            )
        await ctx.send(embeds=embed)

    @emoji_board.subcommand(name="edit")
    @option("The name of your emoji board", autocomplete=True)
    @option("The new name for your emoji board")
    @option("The text channel for sending messages", channel_types=[ChannelType.GUILD_TEXT])
    @option("Count to add emoji to board", min_value=1)
    @option("Count to remove emoji from board", min_value=0)
    @option("Should be emoji board be frozen")
    @option("The embed color for board message", min_lenght=6, max_lenght=6)
    async def edit_emoji_board(
        self,
        ctx: CommandContext,
        name: str,
        new_name: str = None,
        channel: Channel = None,
        to_add: int = None,
        to_remove: int = None,
        freeze: bool = None,
        embed_color: str = None,
    ):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        emoji_board = guild_data.get_emoji_board(name)
        if emoji_board is None:
            raise  # TODO: Exception

        if new_name is not None:
            emoji_board.name = new_name
        if channel is not None:
            emoji_board.channel_id = int(channel.id)  # TODO: Check channel perms
        if to_add is not None:
            emoji_board.to_add = to_add
        if to_remove is not None:
            emoji_board.to_remove = to_remove
        if freeze is not None:
            emoji_board.freeze = freeze
        if embed_color:
            if not re.fullmatch(r"[a-zA-z0-9]+", embed_color):
                raise Exception("Invalid color!")
            emoji_board.embed_color = embed_color

        await emoji_board.update()
        await ctx.send("Emoji board edited!")

    @emoji_board.subcommand(name="add_emoji")
    @option("The name of your emoji board", autocomplete=True)
    @option("The emoji to add")
    async def add_emoji(self, ctx: CommandContext, name: str, emoji: str):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        if guild_data.emoji_boards:
            for _board in guild_data.emoji_boards:
                if emoji in _board.emojis:
                    raise  # Emoji taken

        emoji_board = guild_data.get_emoji_board(name)
        if emoji_board is None:
            raise  # TODO: Exception

        emoji_board.emojis.append(emoji)
        await emoji_board.update()
        await ctx.send("Emoji added!")

    @emoji_board.subcommand(name="remove_emoji")
    @option("The name of your emoji board", autocomplete=True)
    @option("The emoji to remove", autocomplete=True)
    async def remove_emoji(self, ctx: CommandContext, name: str, emoji: str):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        emoji_board = guild_data.get_emoji_board(name)

        if emoji_board is None:
            raise  # TODO: Exception
        if emoji not in emoji_board.emojis:
            raise

        emoji_board.emojis.remove(emoji)
        await emoji_board.update()
        await ctx.send("Emoji removed!")

    @emoji_board.subcommand(name="leaderboard")
    @option("The name of your emoji board", autocomplete=True)
    async def leaderboard(self, ctx: CommandContext, name: str):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        emoji_board = guild_data.get_emoji_board(name)
        if emoji_board is None:
            raise  # TODO: Exception

        data = defaultdict(lambda: 0)
        for message_data in emoji_board.messages:  # TODO: Optimize it
            data[message_data.author_id] += len(message_data.users)

        embed = Embed(
            title="Leaderboard",
            description="\n".join(
                [
                    f"{Mention.USER.format(id=author_id)}: `{count}`"
                    for author_id, count in data.items()
                ]
            ),
        )  # TODO: add emojis to description
        embed.set_footer(text=f"Emoji board name: {emoji_board.name}")
        await ctx.send(embeds=embed)


def setup(client):
    EmojiBoards(client)
