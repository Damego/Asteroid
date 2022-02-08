from datetime import datetime
from re import compile
from typing import Union, List

from discord import (
    VoiceClient,
    Member,
    Embed,
    VoiceState,
    Guild,
    VoiceChannel,
)
from discord.ext.commands import BadArgument
from discord_slash import SlashContext, AutoCompleteContext, SlashCommandOptionType
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_components import Button, ButtonStyle
from discord_slash_components_bridge import ComponentContext, ComponentMessage
import lavalink

from my_utils import (
    AsteroidBot,
    get_content,
    Cog,
    is_enabled,
    BotNotConnectedToVoice,
    NotConnectedToVoice,
    NotPlaying,
    consts,
    NoData,
)


url_rx = compile(r"https?://(?:www\.)?.+")


class LavalinkVoiceClient(VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    """

    def __init__(self, client, channel: VoiceChannel):
        self.client = client
        self.channel = channel

        if not hasattr(self.client, "lavalink"):
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                "localhost", 3678, "testpassword", "us", "default-node"
            )
        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {"t": "VOICE_SERVER_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        lavalink_data = {"t": "VOICE_STATE_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


class Music(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = "🎵"
        self.name = "Music"

    @Cog.listener()
    async def on_ready(self):
        self.bot.lavalink = lavalink.Client(self.bot.user.id)
        self.bot.lavalink.add_node(
            "127.0.0.1", 3678, "testpassword", "ru", "default-node"
        )

    @Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        if member.bot and member.id == self.bot.user.id and after.channel is None:
            return await self._stop_on_leave(member.guild)
        if (
            before.channel is not None
            and 0 < len(before.channel.members) < 2
            and before.channel.members[0].id == self.bot.user.id
        ):
            return await self._stop_on_leave(member.guild)

    async def _stop_on_leave(self, guild: Guild):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(guild.id)
        if player is not None:
            player.queue.clear()
            await player.stop()
        if guild.voice_client is not None:
            await guild.voice_client.disconnect(force=True)

    @slash_subcommand(base="music", name="play", description="Start playing music")
    @is_enabled()
    async def play_music(self, ctx: SlashContext, query: str):
        await self._play_music(ctx, query)

    @slash_subcommand(base="music", name="stop", description="Stop playing music")
    @is_enabled()
    async def stop_music(self, ctx: SlashContext):
        await ctx.defer()

        player = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )
        self.__check_music_status(ctx, player)

        player.queue.clear()
        await player.stop()
        await ctx.voice_client.disconnect(force=True)
        await ctx.send(content["DISCONNECTED_TEXT"])

    @slash_subcommand(base="music", name="pause", description="Pause playing music")
    @is_enabled()
    async def pause_music(self, ctx: SlashContext):
        await ctx.defer()

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
            ctx.guild_id
        )
        content: dict = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        await player.set_pause(True)
        await ctx.send(content["PAUSED_TEXT"])

    @slash_subcommand(base="music", name="resume", description="Resume playing music")
    @is_enabled()
    async def resume_music(self, ctx: SlashContext):
        await ctx.defer()

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
            ctx.guild_id
        )
        content: dict = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        await player.set_pause(False)
        await ctx.send(content["RESUMED_TEXT"])

    @slash_subcommand(base="music", name="repeat", description="Toggle music repeat")
    @is_enabled()
    async def repeat_music(self, ctx: SlashContext):
        await ctx.defer()

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
            ctx.guild_id
        )
        content: dict = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        await player.set_repeat(not player.repeat)
        if not player.repeat:
            await ctx.send(content["REPEAT_OFF_TEXT"])
        else:
            await ctx.send(content["REPEAT_ON_TEXT"])

    @slash_subcommand(base="music", name="skip", description="Skip music")
    @is_enabled()
    async def skip_music(self, ctx: SlashContext):
        await ctx.defer()

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
            ctx.guild_id
        )
        content: dict = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        track = player.queue[0] if player.queue else None
        await player.skip()
        await ctx.send(content["TRACK_SKIPPED_TEXT"])
        if track:
            await self._send_message(ctx, track, content)

    @slash_subcommand(
        base="music",
        name="queue",
        description="Show current queue",
    )
    @is_enabled()
    async def show_queue_musis(self, ctx: SlashContext):
        await ctx.defer(hidden=True)

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
            ctx.guild_id
        )
        content: dict = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        if not player.queue:
            return await ctx.send(content["QUEUE_IS_EMPTY_TEXT"])

        tracks = [
            f"**{count}.** `{track.title}`"
            for count, track in enumerate(player.queue, start=1)
        ]
        embed = Embed(
            title=content["CURRENT_QUEUE_TITLE_TEXT"],
            description="\n".join(tracks),
            color=self.bot.get_embed_color(ctx.guild_id),
        )
        await ctx.send(embed=embed, hidden=True)

    @Cog.listener(name="on_autocomplete")
    async def playlist_autocomplete(self, ctx: AutoCompleteContext):
        choices = None
        if not self.bot.get_transformed_command_name(ctx).startswith("music"):
            return

        if ctx.focused_option == "playlist":
            user_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.author_id)
            if not user_data:
                return
            user_playlists = user_data.get("music_playlists")
            if not user_playlists:
                return
            playlists = [
                playlist
                for playlist in user_playlists
                if playlist.startswith(ctx.user_input)
            ]
            choices = [
                create_choice(name=playlist, value=playlist) for playlist in playlists
            ]
        elif ctx.focused_option == "name":
            user_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.author_id)
            if not user_data:
                return
            user_playlists = user_data.get("music_playlists")
            if not user_playlists:
                return
            input_playlist = ctx.options["playlist"]
            tracks_list = user_playlists[input_playlist]
            choices = [create_choice(name=track, value=track) for track in tracks_list if track.startswith(ctx.user_input)]
        elif ctx.focused_option == "member_playlist":
            member_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.guild.get_member(int(ctx.options["member"])).id)
            if not member_data:
                return
            member_playlists = member_data.get("music_playlists")
            if not member_playlists:
                return

            playlists = [
                playlist
                for playlist in member_playlists
                if playlist.startswith(ctx.user_input)
            ]
            choices = [
                create_choice(name=playlist, value=playlist) for playlist in playlists
            ]
        if choices:
            await ctx.populate(choices)

    @slash_subcommand(
        base="music",
        subcommand_group="playlist",
        name="add_track",
        description="Add a current song to your playlist",
        options=[
            create_option(
                name="playlist",
                description="Your playlist. If not exists it creates new one",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="query",
                description="The query if bot is not playing",
                option_type=SlashCommandOptionType.STRING,
                required=False,
            ),
            create_option(
                name="hidden",
                description="Should be message hidden or not",
                option_type=SlashCommandOptionType.BOOLEAN,
                required=False,
            ),
        ],
    )
    @is_enabled()
    async def music_add_to_playlist(
        self, ctx: SlashContext, playlist: str, query: str = None, hidden: bool = False
    ):
        collection = self.bot.get_guild_users_collection(ctx.guild_id)
        if not query:
            player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
                ctx.guild_id
            )
            if not player:
                raise NotPlaying
            query = player.current.title

        collection.update_one(
            {"_id": str(ctx.author_id)},
            {"$push": {f"music_playlists.{playlist}": query}},
            upsert=True,
        )
        content = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))["MUSIC_PLAYLIST"]
        embed = Embed(
            title=content["PLAYLIST_UPDATE_TITLE_TRACK"].format(playlist=playlist),
            description=content["ADDED_TEXT"].format(query=query),
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        await ctx.send(embed=embed, hidden=hidden)

    @slash_subcommand(
        base="music",
        subcommand_group="playlist",
        name="delete_track",
        description="Deletes a song from your playlist",
        options=[
            create_option(
                name="playlist",
                description="Your playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="name",
                description="The name of track in playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
        ],
    )
    @is_enabled()
    async def music_delete_from_playlist(
        self, ctx: SlashContext, playlist: str, name: str
    ):
        await ctx.defer(hidden=True)
        user_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.author_id)
        if not user_data:
            raise NoData
        user_playlists = user_data.get("music_playlists")
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        self.bot.mongo.update_user(
            ctx.guild_id,
            ctx.author_id,
            "$pull",
            {f"music_playlists.{playlist}": name}
        )
        content = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))["MUSIC_PLAYLIST"]
        await ctx.send(content["MUSIC_DELETED"].format(name=name, playlist=playlist), hidden=True)

    @slash_subcommand(
        base="music",
        subcommand_group="playlist",
        name="play",
        description="Plays/adds to queue your playlist",
        options=[
            create_option(
                name="playlist",
                description="Your playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def music_play_playlist(self, ctx: SlashContext, playlist: str):
        user_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.author_id)
        if not user_data:
            raise NoData
        user_playlists = user_data.get("music_playlists")
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        await self._play_music(ctx, playlist_data, is_playlist=True)

    @slash_subcommand(
        base="music",
        subcommand_group="playlist",
        name="info",
        description="Shows your playlist",
        options=[
            create_option(
                name="playlist",
                description="Your playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="hidden",
                description="Should be message hidden or not",
                option_type=SlashCommandOptionType.BOOLEAN,
                required=False,
            ),
        ],
    )
    @is_enabled()
    async def show_user_playlist(
        self, ctx: SlashContext, playlist: str, hidden: bool = True
    ):
        await ctx.defer(hidden=hidden)
        user_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.author_id)
        if not user_data:
            raise NoData
        user_playlists = user_data.get("music_playlists")
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        content = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )["MUSIC_PLAYLIST"]
        embed = Embed(
            title=content["PLAYLIST_TITLE_TEXT"].format(playlist=playlist),
            description="",
            color=self.bot.get_embed_color(ctx.guild_id),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        for count, track in enumerate(playlist_data, start=1):
            embed.description += f"{count}. `{track}`\n"

        await ctx.send(embed=embed, hidden=hidden)

    @slash_subcommand(
        base="music",
        subcommand_group="playlist",
        name="copy",
        description="Copies a user playlist to your playlist",
        options=[
            create_option(
                name="member",
                description="The Member to copy playlist",
                option_type=SlashCommandOptionType.USER,
                required=True
            ),
            create_option(
                name="member_playlist",
                description="Playlist of member",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="playlist",
                description="Your playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            ),
        ]
    )
    async def copy_member_playlist(self, ctx: SlashContext, member: Member, member_playlist: str, playlist: str):
        await ctx.defer(hidden=True)
        user_data = self.bot.mongo.get_user_data(ctx.guild_id, member.id)
        if not user_data:
            raise NoData
        user_playlists = user_data.get("music_playlists")
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(member_playlist)
        if not playlist_data:
            raise NoData

        self.bot.mongo.update_user(
            ctx.guild_id,
            ctx.author_id,
            "$push",
            {f"music_playlists.{playlist}": {"$each": playlist_data}}
        )
        content = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )["MUSIC_PLAYLIST"]
        await ctx.send(content["PLAYLIST_COPIED"], hidden=True)

    @slash_subcommand(
        base="music",
        subcommand_group="playlist",
        name="delete",
        description="Deletes your playlist",
        options=[
            create_option(
                name="playlist",
                description="Your playlist",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    async def delete_user_playlist(
        self, ctx: SlashContext, playlist: str
    ):
        await ctx.defer(hidden=True)
        user_data = self.bot.mongo.get_user_data(ctx.guild_id, ctx.author_id)
        if not user_data:
            raise NoData
        user_playlists = user_data.get("music_playlists")
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        content = get_content(
            "MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id)
        )["MUSIC_PLAYLIST"]

        await ctx.send(
            content["PLAYLIST_DELETE_TEXT"].format(playlist=playlist)
        )

        self.bot.mongo.update_user(
            ctx.guild_id,
            ctx.author_id,
            "$unset",
            {f"music_playlists.{playlist}": ""}
        )

    async def _play_music(
        self, ctx: SlashContext, query: Union[str, List[str]], is_playlist: bool = False
    ):
        await ctx.defer()

        if not ctx.author.voice:
            raise NotConnectedToVoice
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("MUSIC_COMMANDS", lang)

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(
            ctx.guild_id
        )
        if player is None:
            player = self.bot.lavalink.player_manager.create(
                ctx.guild_id, endpoint=str(ctx.guild.region)
            )

        if not ctx.voice_client:
            player.store("channel", ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)

        track = tracks = None
        if isinstance(query, List) and is_playlist:
            tracks = [
                await self.__get_tracks(ctx, player, content, _query)
                for _query in query
            ]
        else:
            track = await self.__get_tracks(ctx, player, content, query)

        await self._added_to_queue(ctx, track or tracks, content)

        if not player.is_playing:
            await self._send_message(ctx, track or tracks[0], content)
            await player.play()

    async def __get_tracks(self, ctx: SlashContext, player, content: dict, query: str):
        tracks = track = None

        if not url_rx.match(query):
            query = f"ytsearch:{query}"
        results = await player.node.get_tracks(query)
        if not results or not results["tracks"]:
            return await ctx.send(content["MUSIC_NOT_FOUND_TEXT"])

        if results["loadType"] == "PLAYLIST_LOADED":
            tracks = [
                lavalink.AudioTrack(track_data, ctx.author)
                for track_data in results["tracks"]
            ]
            for track in tracks:
                player.add(requester=ctx.author, track=track)
        else:
            track = lavalink.AudioTrack(results["tracks"][0], ctx.author)
            player.add(requester=ctx.author, track=results["tracks"][0])

        return tracks or track

    async def _added_to_queue(
        self,
        ctx: SlashContext,
        tracks: Union[List[lavalink.AudioTrack], lavalink.AudioTrack],
        content: dict,
    ):
        if isinstance(tracks, lavalink.AudioTrack):
            tracks = [tracks]
        tracks_titles = [f"`{track.title}`" for track in tracks]

        description = content["ADDED_IN_QUEUE_DESCRIPTION_TEXT"].format(
            tracks_amount=len(tracks), tracks="\n".join(tracks_titles)
        )
        embed = Embed(
            title=content["ADDED_IN_QUEUE_TITLE_TEXT"],
            description=description,
            color=self.bot.get_embed_color(ctx.guild_id),
        )
        await ctx.send(embed=embed)

    async def _send_message(
        self, ctx: SlashContext, track: lavalink.AudioTrack, content: dict
    ):
        embed = await self._get_music_info(ctx, track, content)
        if not ctx.responded:
            await ctx.send(embed=embed)
        else:
            await ctx.channel.send(embed=embed)

    async def _get_music_info(
        self, ctx: SlashContext, track: lavalink.AudioTrack, content: dict
    ) -> Embed:
        if not track.stream:
            duration = self._get_track_duration(track)
        else:
            duration = content["LIVE_TEXT"]

        embed = Embed(
            title=content["PLAYING_TEXT"], color=self.bot.get_embed_color(ctx.guild.id)
        )
        embed.add_field(
            name=content["NAME_TEXT"],
            value=f"[{track.title}]({track.uri})",
            inline=False,
        )
        embed.add_field(name=content["DURATION_TEXT"], value=duration, inline=False)
        embed.set_footer(
            text=content["REQUESTED_BY_TEXT"].format(ctx.author.display_name),
            icon_url=ctx.author.avatar_url,
        )
        embed.set_thumbnail(
            url=f"https://i.ytimg.com/vi/{track.identifier}/maxresdefault.jpg"
        )

        return embed

    def _get_track_duration(self, track: Union[lavalink.AudioTrack, int]):
        if isinstance(track, lavalink.AudioTrack):
            original_duration = track.duration // 1000
        else:
            original_duration = track // 1000

        duration_hours = original_duration // 3600
        duration_minutes = (original_duration // 60) % 60
        duration_seconds = original_duration % 60
        return f"{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}"

    def __check_music_status(self, ctx: SlashContext, player: lavalink.DefaultPlayer):
        if player is None:
            raise BotNotConnectedToVoice
        if not player.is_connected:
            raise BotNotConnectedToVoice
        if not ctx.author.voice or ctx.author.voice.channel.id != int(
            player.channel_id
        ):
            raise NotConnectedToVoice
        if not player.is_playing:
            raise NotPlaying


def setup(bot):
    bot.add_cog(Music(bot))
