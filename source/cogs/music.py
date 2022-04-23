from datetime import datetime
from re import compile
from typing import List, Union

import lavalink
from discord import Embed, Guild, Member, Permissions, VoiceChannel, VoiceClient, VoiceState
from discord.ext.commands import BotMissingPermissions
from discord_slash import AutoCompleteContext, SlashCommandOptionType, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import (
    AsteroidBot,
    BotNotConnectedToVoice,
    Cog,
    NoData,
    NotConnectedToVoice,
    NotPlaying,
    bot_owner_or_permissions,
    get_content,
    is_enabled,
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
        self.lavalink = client.lavalink

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
        self.bot.lavalink.add_node("127.0.0.1", 3678, "testpassword", "ru", "default-node")

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
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
            "MUSIC_COMMANDS", await self.bot.get_guild_bot_lang(ctx.guild_id)
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

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content(
            "MUSIC_COMMANDS", await self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        await player.set_pause(True)
        await ctx.send(content["PAUSED_TEXT"])

    @slash_subcommand(base="music", name="resume", description="Resume playing music")
    @is_enabled()
    async def resume_music(self, ctx: SlashContext):
        await ctx.defer()

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content(
            "MUSIC_COMMANDS", await self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        self.__check_music_status(ctx, player)

        await player.set_pause(False)
        await ctx.send(content["RESUMED_TEXT"])

    @slash_subcommand(base="music", name="repeat", description="Toggle music repeat")
    @is_enabled()
    async def repeat_music(self, ctx: SlashContext):
        await ctx.defer()

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content(
            "MUSIC_COMMANDS", await self.bot.get_guild_bot_lang(ctx.guild_id)
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

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content(
            "MUSIC_COMMANDS", await self.bot.get_guild_bot_lang(ctx.guild_id)
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
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content("MUSIC_COMMANDS", guild_data.configuration.language)

        self.__check_music_status(ctx, player)

        if not player.queue:
            return await ctx.send(content["QUEUE_IS_EMPTY_TEXT"])

        tracks = [
            f"**{count}.** `{track.title}`" for count, track in enumerate(player.queue, start=1)
        ]
        embed = Embed(
            title=content["CURRENT_QUEUE_TITLE_TEXT"],
            description=f"**{content['CURRENT_SONG_TEXT']}:** `{player.current.title}`\n"
            + "\n".join(tracks),
            color=guild_data.configuration.embed_color,
        )
        await ctx.send(embed=embed, hidden=True)

    @slash_subcommand(
        base="music",
        name="force_stop",
        description="Use this command if bot doesn't connect or doesn't play music",
    )
    @bot_owner_or_permissions(move_members=True)
    @is_enabled()
    async def music_force_stop(self, ctx: SlashContext):
        await ctx.defer(hidden=True)

        player = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if player is not None:
            player.queue.clear()
            await player.stop()
        try:
            await ctx.voice_client.disconnect(force=True)
        except Exception:
            await ctx.send(":x:")
        else:
            await ctx.send(":white_check_mark:")

    @Cog.listener(name="on_autocomplete")
    async def playlist_autocomplete(self, ctx: AutoCompleteContext):
        choices = None
        if ctx.name not in ["music", "global"]:
            return

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        global_data = await self.bot.mongo.get_global_data()

        if ctx.focused_option == "playlist":
            user_guild_data = await guild_data.get_user(ctx.author_id)
            user_global_data = await global_data.get_user(ctx.author_id)
            all_playlists = user_guild_data.music_playlists | user_global_data.music_playlists

            playlists = [
                playlist for playlist in all_playlists if playlist.startswith(ctx.user_input)
            ]

            choices = [create_choice(name=playlist, value=playlist) for playlist in playlists]
        elif ctx.focused_option == "name":
            user_guild_data = await guild_data.get_user(ctx.author_id)
            user_global_data = await global_data.get_user(ctx.author_id)
            if not user_guild_data.music_playlists and not user_global_data.music_playlists:
                return

            input_playlist = ctx.options["playlist"]
            all_playlists = user_guild_data.music_playlists | user_global_data.music_playlists
            tracks_list = all_playlists.get(input_playlist)
            choices = [
                create_choice(name=track, value=track)
                for track in tracks_list
                if track.startswith(ctx.user_input)
            ]
        elif ctx.focused_option == "member_playlist":
            member_data = await guild_data.get_user(int(ctx.options["member"]))

            playlists = [
                playlist
                for playlist in member_data.music_playlists
                if playlist.startswith(ctx.user_input)
            ]
            choices = [create_choice(name=playlist, value=playlist) for playlist in playlists]
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
        if not query:
            player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
            if not player:
                raise NotPlaying
            query = player.current.title

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if playlist.endswith("GLOBAL"):
            data = await self.bot.mongo.get_global_data()
        else:
            data = guild_data

        user_data = await data.get_user(ctx.author_id)
        await user_data.add_track_to_playlist(playlist, query)

        content = get_content("MUSIC_COMMANDS", guild_data.configuration.language)["MUSIC_PLAYLIST"]
        embed = Embed(
            title=content["PLAYLIST_UPDATE_TITLE_TRACK"].format(playlist=playlist),
            description=content["ADDED_TEXT"].format(query=query),
            color=guild_data.configuration.embed_color,
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
    async def music_delete_from_playlist(self, ctx: SlashContext, playlist: str, name: str):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if playlist.endswith("GLOBAL"):
            data = await self.bot.mongo.get_global_data()
        else:
            data = guild_data

        user_data = await data.get_user(ctx.author_id)
        user_playlists = user_data.music_playlists
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        await user_data.remove_track_from_playlist(playlist, name)

        content = get_content("MUSIC_COMMANDS", guild_data.configuration.language)["MUSIC_PLAYLIST"]
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
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if playlist.endswith("GLOBAL"):
            data = await self.bot.mongo.get_global_data()
        else:
            data = guild_data

        user_data = await data.get_user(ctx.author_id)
        user_playlists = user_data.music_playlists
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
    async def show_user_playlist(self, ctx: SlashContext, playlist: str, hidden: bool = True):
        await ctx.defer(hidden=hidden)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if playlist.endswith("GLOBAL"):
            data = await self.bot.mongo.get_global_data()
        else:
            data = guild_data

        user_data = await data.get_user(ctx.author_id)
        user_playlists = user_data.music_playlists
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        content = get_content("MUSIC_COMMANDS", guild_data.configuration.language)["MUSIC_PLAYLIST"]
        embed = Embed(
            title=content["PLAYLIST_TITLE_TEXT"].format(playlist=playlist),
            description="",
            color=guild_data.configuration.embed_color,
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
                required=True,
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
        ],
    )
    @is_enabled()
    async def copy_member_playlist(
        self, ctx: SlashContext, member: Member, member_playlist: str, playlist: str
    ):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        member_data = await guild_data.get_user(member.id)
        member_playlists = member_data.music_playlists
        if not member_playlists:
            raise NoData
        playlist_data = member_playlists.get(member_playlist)
        if not playlist_data:
            raise NoData

        if playlist.endswith("GLOBAL"):
            data = await self.bot.mongo.get_global_data()
        else:
            data = guild_data
        user_data = await data.get_user(ctx.author_id)
        await user_data.add_many_tracks(playlist, playlist_data)

        content = get_content("MUSIC_COMMANDS", guild_data.configuration.language)["MUSIC_PLAYLIST"]
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
    async def delete_user_playlist(self, ctx: SlashContext, playlist: str):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if playlist.endswith("GLOBAL"):
            data = await self.bot.mongo.get_global_data()
        else:
            data = guild_data

        user_data = await data.get_user(ctx.author_id)
        user_playlists = user_data.music_playlists
        if not user_playlists:
            raise NoData
        playlist_data = user_playlists.get(playlist)
        if not playlist_data:
            raise NoData

        content = get_content("MUSIC_COMMANDS", guild_data.configuration.language)["MUSIC_PLAYLIST"]

        await ctx.send(content["PLAYLIST_DELETE_TEXT"].format(playlist=playlist))

        await user_data.remove_playlist(playlist)

    def __can_connect(self, ctx: SlashContext):
        bot_user: Member = ctx.guild.me
        if bot_user.guild_permissions.administrator:
            return True

        channel: VoiceChannel = ctx.author.voice.channel
        permissions: Permissions = channel.permissions_for(ctx.guild.me)
        return permissions.connect

    async def _play_music(
        self, ctx: SlashContext, query: Union[str, List[str]], is_playlist: bool = False
    ):
        await ctx.defer()

        if not ctx.author.voice:
            raise NotConnectedToVoice
        if not self.__can_connect(ctx):
            raise BotMissingPermissions(["Connect"])

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("MUSIC_COMMANDS", lang)

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if player is None:
            player = self.bot.lavalink.player_manager.create(
                ctx.guild_id, endpoint=str(ctx.guild.region)
            )

        if not ctx.voice_client:
            player.store("channel", ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)

        tracks = None
        if isinstance(query, List) and is_playlist:
            tracks = [await self.__get_tracks(ctx, player, _query) for _query in query]
        else:
            tracks = [await self.__get_tracks(ctx, player, query)]

        await self._added_to_queue(ctx, tracks, content)

        if not player.is_playing:
            await self._send_message(ctx, tracks[0], content)
            await player.play()

    async def __get_tracks(self, ctx: SlashContext, player, query: str):
        tracks = track = None

        if not url_rx.match(query):
            query = f"ytsearch:{query}"
        results = await player.node.get_tracks(query)
        if not results or not results["tracks"]:
            raise NoData  # * Should be here raising error?

        if results["loadType"] == "PLAYLIST_LOADED":
            tracks = [
                lavalink.AudioTrack(track_data, ctx.author) for track_data in results["tracks"]
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
            color=await self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow(),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    async def _send_message(self, ctx: SlashContext, track: lavalink.AudioTrack, content: dict):
        embed = await self._get_music_info(ctx, track, content)
        if not ctx.responded:
            await ctx.send(embed=embed)
        else:
            await ctx.channel.send(embed=embed)

    async def _get_music_info(
        self, ctx: SlashContext, track: lavalink.AudioTrack, content: dict
    ) -> Embed:
        duration = content["LIVE_TEXT"] if track.stream else self._get_track_duration(track)

        embed = Embed(
            title=content["PLAYING_TEXT"],
            color=await self.bot.get_embed_color(ctx.guild.id),
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
        embed.set_thumbnail(url=f"https://i.ytimg.com/vi/{track.identifier}/maxresdefault.jpg")

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
        if not ctx.author.voice or ctx.author.voice.channel.id != int(player.channel_id):
            raise NotConnectedToVoice
        if not player.is_playing:
            raise NotPlaying


def setup(bot):
    bot.add_cog(Music(bot))
