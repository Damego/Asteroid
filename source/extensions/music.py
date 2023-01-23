import re

from interactions import Color, Embed, Extension, option
from interactions.ext.lavalink import Lavalink, Player
from lavalink import AudioTrack

from core import Asteroid, BotException, command, listener
from core.context import CommandContext

url_pattern = re.compile(r"https?://(?:www\.)?.+")


def _is_url(string: str):
    return url_pattern.match(string) is not None


class Music(Extension):
    def __init__(self, client: Asteroid):
        self.client: Asteroid = client
        self.lavalink: Lavalink = None  # noqa

    @listener()
    async def on_start(self):
        self.lavalink = Lavalink(self.client)
        self.lavalink.add_node("127.0.0.1", 36790, "testpassword", "eu")

    @command()
    async def music(self, ctx: CommandContext):
        """The base for music command"""

    @music.subcommand()
    @option("The query to search or url to music")
    async def play(self, ctx: CommandContext, query: str):
        """Play the music"""
        player = await self.check_state(ctx)
        if player is False:
            return

        await ctx.defer()

        voice_state = ctx.author.voice_state
        player = await self.lavalink.connect(
            voice_state.guild_id, voice_state.channel_id, self_deaf=True
        )

        if _is_url(query):
            tracks = await player.get_tracks(query)
        else:
            tracks = await player.search_youtube(query)

        if not tracks:
            return await ctx.send(ctx.translate("TRACKS_NOT_FOUND"), ephemeral=True)

        track = tracks[0]
        player.add(track, requester=int(ctx.author.id))

        await ctx.send(embeds=self.build_added_to_queue_embed(ctx, track))
        if player.is_playing:
            return

        await player.play()
        await ctx.send(embeds=self.build_playing_embed(ctx, track))

    @music.subcommand()
    @option("The query to search or url to music")
    async def add_to_queue(self, ctx: CommandContext, query: str):
        """Adds track to the queue"""
        player = await self.check_state(ctx)
        if not player:
            return

        await ctx.defer()

        if _is_url(query):
            tracks = await player.get_tracks(query)
        else:
            tracks = await player.search_youtube(query)

        if not tracks:
            return await ctx.send("Nothing found", ephemeral=True)

        track = tracks[0]
        player.add(track, requester=int(ctx.author.id))

        await ctx.send(embeds=self.build_added_to_queue_embed(ctx, track))

    @music.subcommand()
    async def stop(self, ctx: CommandContext):
        """Stops the playing"""
        player = await self.check_state(ctx)
        if not player:
            return

        await player.stop()

        embed = Embed(title="Playing was stopped", color=Color.BLURPLE)
        await ctx.send(embeds=embed)

    @music.subcommand()
    async def toggle_playing(self, ctx: CommandContext):
        """Pauses/resumes playing"""
        player = await self.check_state(ctx)
        if not player:
            return

        current_state = not player.paused
        await player.set_pause(current_state)

        pause_resume_text = "resumed" if not current_state else "paused"
        embed = Embed(title=f"Playing is {pause_resume_text}", color=Color.BLURPLE)

        await ctx.send(embeds=embed)

    @music.subcommand()
    async def queue(self, ctx: CommandContext):
        """Shows the current queue"""
        player = await self.check_state(ctx)
        if not player:
            return

        if not player.queue:
            embed = Embed(title="Empty queue", color=Color.BLURPLE)
            return await ctx.send(embeds=embed, ephemeral=True)

        embed = Embed(
            title=f"{ctx.guild.name}'s current queue", description="", color=Color.BLURPLE
        )

        for index, track in enumerate(player.queue, start=1):
            embed.description += f"**` {index} `** `{track.title}` \n"

        await ctx.send(embeds=embed, ephemeral=True)

    @music.subcommand()
    @option("Track to be skipped to", autocomplete=True, required=False)
    async def skip(self, ctx: CommandContext, track_name: str = None):
        player = await self.check_state(ctx)
        if not player:
            return

        queue = player.queue
        if not queue:
            return await ctx.send("Empty queue", ephemeral=True)

        if track_name is not None:
            for i in range(len(queue) - 1):
                if queue[i + 1].title == track_name:
                    break
                queue.pop(0)

        await player.skip()

        embed = Embed(title="Track was skipped", color=Color.BLURPLE)
        await ctx.send(embeds=embed)

    async def check_state(self, ctx: CommandContext) -> Player | None:
        voice_state = ctx.author.voice_state

        if not voice_state or not voice_state.joined:
            raise BotException("USER_NOT_CONNECTED_TO_CHANNEL")

        player = self.lavalink.get_player(voice_state.guild_id)
        if player and player.channel_id != voice_state.channel_id:
            raise BotException("PLAYER_IS_BUSY", channel=voice_state.channel.mention)

        return player

    def build_playing_embed(self, ctx: CommandContext, track: AudioTrack) -> Embed:
        embed = Embed(title=ctx.translate("NOW_PLAYING"), color=Color.BLURPLE)
        embed.set_thumbnail(f"https://i.ytimg.com/vi/{track.identifier}/maxresdefault.jpg")
        embed.add_field(name=ctx.translate("TRACK_NAME"), value=f"[{track.title}]({track.uri})")
        embed.add_field(name=ctx.translate("TRACK_DURATION"), value=self.get_track_duration(track))
        embed.set_footer(
            text=ctx.translate("ADDED_BY_EMBED_FOOTER", ctx.author.name),
            icon_url=ctx.author.user.avatar_url,
        )

        return embed

    @staticmethod
    def build_added_to_queue_embed(
        ctx: CommandContext, tracks: list[AudioTrack] | AudioTrack
    ) -> Embed:
        tracks = tracks if isinstance(tracks, list) else [tracks]

        embed = Embed(
            title=ctx.translate("QUEUE_UPDATE_EMBED_TITLE"),
            description=ctx.translate("QUEUE_WAS_ADDED", tracks=len(tracks)),
            color=Color.BLURPLE,
        )
        embed.set_footer(
            text=ctx.translate("ADDED_BY_EMBED_FOOTER", ctx.author.name),
            icon_url=ctx.author.user.avatar_url,
        )

        return embed

    @staticmethod
    def get_track_duration(track: AudioTrack):
        total_seconds = track.duration // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds // 60) % 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"


def setup(client: Asteroid):
    Music(client)
