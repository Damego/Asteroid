import datetime
from asyncio import get_event_loop, sleep

from core import Asteroid, GuildEmojiBoard
from interactions import (
    Channel,
    ChannelType,
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


class EmojiBoards(Extension):
    def __init__(self, client):
        self.client: Asteroid = client

    @listener()
    async def on_message_reaction_add(self, reaction: MessageReaction):
        guild_data = await self.client.database.get_guild(int(reaction.guild_id))
        emoji = reaction.emoji
        for emoji_board in guild_data.emoji_boards:
            if str(emoji) == emoji_board.emoji:
                break
        else:
            return
        channel: Channel = await self.client.get(Channel, object_id=int(reaction.channel_id))
        message = await channel.get_message(reaction.message_id)
        if message.author.id == reaction.user_id:
            return await message.remove_reaction_from(emoji, reaction.user_id)

        for _reaction in message.reactions:
            if _reaction.emoji == emoji:
                break

        count = _reaction.count

        if count < emoji_board.to_add:
            return
        if count == emoji_board.to_add:
            return await self.__add_message(message, emoji_board, count)

        await self.__update_message(message, emoji_board, count)

    @listener()
    async def on_raw_message_reaction_remove(self, reaction: MessageReaction):
        guild_data = await self.client.database.get_guild(int(reaction.guild_id))
        emoji = reaction.emoji
        for emoji_board in guild_data.emoji_boards:
            if str(emoji) == emoji_board.emoji:
                break
        else:
            return
        channel: Channel = await self.client.get(Channel, object_id=int(reaction.channel_id))
        message = await channel.get_message(reaction.message_id)

        for _reaction in message.reactions:
            if _reaction.emoji == emoji:
                break

        count = _reaction.count

        if count > emoji_board.to_remove:
            return
        if count == emoji_board.to_remove:
            return await self.__remove_message(message, emoji_board)

        await self.__update_message(message, emoji_board, count)

    async def __add_message(self, message: Message, emoji_board: GuildEmojiBoard, count: int):
        if message.embeds:
            embed = message.embeds[0]
            embed.description = embed.description or ""
        else:
            embed = Embed(
                description=message.content,
                color=Color.blurple(),  # TODO: Custom color for every emoji board?
            )
        embed.description += f"\n\n[**Go to message**]({message.url})"
        embed.timestamp = datetime.datetime.utcnow().isoformat()
        embed.set_author(name=message.author.username, icon_url=message.author.avatar_url)
        embed.set_footer(text=f"Emoji board name: {emoji_board.name}")

        channel = await self.client.get(Channel, object_id=emoji_board.channel_id)
        board_message = await channel.send(f"{emoji_board.emoji} | {count}", embeds=embed)

        emoji_board.add_message(
            message_id=int(message.id), channel_message_id=int(board_message.id)
        )
        await emoji_board.update()

    async def __update_message(self, message: Message, emoji_board: GuildEmojiBoard, count: int):
        for _message in emoji_board.messages:
            if _message.message_id == int(message.id):
                break
        else:
            return print("wat")

        channel: Channel = await self.client.get(Channel, object_id=emoji_board.channel_id)
        board_message = await channel.get_message(_message.channel_message_id)
        await board_message.edit(f"{emoji_board.emoji} | {count}")

    async def __remove_message(self, message: Message, emoji_board: GuildEmojiBoard):
        _message = emoji_board.get_message(message_id=int(message.id))

        channel: Channel = await self.client.get(Channel, object_id=emoji_board.channel_id)
        board_message = await channel.get_message(_message.channel_message_id)
        await board_message.delete(
            "[EmojiBoard] Remove message because it has less reaction that needed."
        )

        emoji_board.remove_message(message=_message)
        await emoji_board.update()

    @command()
    async def emoji_board(self, ctx: CommandContext):
        ...

    @emoji_board.subcommand(name="create")
    @option("The name for your emoji board")
    @option("The text channel for sending messages", channel_types=[ChannelType.GUILD_TEXT])
    @option("The emoji for board")
    @option("Count to add emoji to board", min_value=1)
    @option("Count to remove emoji from board", min_value=0)
    async def create_emoji_board(
        self,
        ctx: CommandContext,
        name: str,
        channel: Channel,
        emoji: str,
        to_add: int = 3,
        to_remove: int = 2,
    ):
        """Create a new emoji board"""

        async def remove_message(message: Message, timeout: int):
            await sleep(timeout)
            await message.delete()

        await ctx.defer()

        try:
            message = await channel.send("Test message to check bot permission")
        except LibraryException:
            return await ctx.send("Bot doesn't have permission to that channel!")
        loop = get_event_loop()
        loop.create_task(remove_message(message, 5))

        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        await guild_data.add_emoji_board(
            name=name, channel_id=int(channel.id), emoji=emoji, to_add=to_add, to_remove=to_remove
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
    @option("The emoji for board")
    @option("Count to add emoji to board", min_value=1)
    @option("Count to remove emoji from board", min_value=0)
    async def edit_emoji_board(
        self,
        ctx: CommandContext,
        name: str,
        new_name: str = None,
        channel: Channel = None,
        emoji: str = None,
        to_add: int = None,
        to_remove: int = None,
    ):
        await ctx.defer()
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        emoji_board = await guild_data.get_emoji_board(name)
        if emoji_board is None:
            raise  # TODO: Exception

        if new_name is not None:
            emoji_board.name = new_name
        if channel is not None:
            emoji_board.channel_id = int(channel.id)  # TODO: Check channel perms
        if emoji is not None:
            emoji_board.emoji = emoji
        if to_add is not None:
            emoji_board.to_add = to_add
        if to_remove is not None:
            emoji_board.to_remove = to_remove

        await emoji_board.update()
        await ctx.send("Emoji board edited!")


def setup(client):
    EmojiBoards(client)
