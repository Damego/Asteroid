from asyncio import AbstractEventLoop
from typing import List, Dict

import discord

from .errors import NotConnectedToVoice, NotPlaying, EmptyQueue
from .utils import get_video_data
from .models import Song


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.queue: Dict[int, List[Song]] = {}
        self.players: List[MusicPlayer] = []

    def create_player(self, ctx, ffmpeg_error_betterfix: bool = False, ffmpeg_error_fix: bool = False):
        if not ctx.voice_client:
            raise NotConnectedToVoice("Cannot create the player because bot is not connected to voice")

        player = MusicPlayer(ctx, self, ffmpeg_error_betterfix, ffmpeg_error_fix)
        self.players.append(player)
        return player

    def get_player(self, guild_id: int = None, channel_id: int = None):
        for player in self.players:
            if player.guild_id == guild_id or player.voice.channel.id == channel_id:
                return player
        return None


class MusicPlayer:
    def __init__(self, ctx, music: Music, ffmpeg_error_betterfix: bool = False, ffmpeg_error_fix: bool = False):
        self.bot = music.bot
        self.ctx = ctx
        self.guild_id: int = ctx.guild.id
        self.music = music
        self.voice: discord.VoiceClient = ctx.voice_client
        self.loop: AbstractEventLoop = ctx.bot.loop
        self.is_playing = False
        self._previous_song = None

        if self.guild_id not in self.music.queue:
            self.music.queue[self.guild_id] = []

        if ffmpeg_error_betterfix:
            self.ffmpeg_opts = {"options": "-vn -loglevel quiet -hide_banner -nostats",
                                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"}
        elif ffmpeg_error_fix:
            self.ffmpeg_opts = {"options": "-vn",
                                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"}
        else:
            self.ffmpeg_opts = {"options": "-vn", "before_options": "-nostdin"}

    def _check_queue(self):
        previous_song = None
        print('in _check_queue')
        try:
            current_song = self.music.queue[self.guild_id][0]
        except IndexError:
            return
        if not current_song.is_looping:
            print('is not looping')
            try:
                previous_song = self.music.queue[self.guild_id].pop(0)
                current_song = self.music.queue[self.guild_id][0]
            except IndexError:
                print('index error')
                return
            if self.music.queue[self.guild_id]:
                print('creating task')
                self.loop.create_task(self._dispatch_on_error_event(previous_song, current_song))
                self._play_track()
        else:
            print('is looping')
            self.loop.create_task(self._dispatch_on_error_event(previous_song, current_song))
            self._play_track()

    async def _dispatch_on_error_event(self, previous_song, current_song):
        print('dispatching')
        await self.bot.dispatch('music_error', previous_song, current_song)
        print('dispatched')

    def _play_track(self):
        if self._previous_song == self.music.queue[self.guild_id][0]:
            self._previous_song = None
            del self.music.queue[self.guild_id][0]

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(self.music.queue[self.guild_id][0].source, **self.ffmpeg_opts))
        self.voice.play(source, after=lambda error: self._check_queue())
        self.is_playing = True
        song = self.music.queue[self.guild_id][0]
        return song

    def disable(self):
        self.music.players.remove(self)

    async def add_to_queue(self, url, search: bool = False, bettersearch: bool = False):
        song = await get_video_data(url, search, bettersearch, self.loop)
        self.music.queue[self.guild_id].append(song)
        return song

    async def play(self):
        song = self._play_track()
        return song

    async def skip(self, force=False):
        if not self.music.queue[self.guild_id]:
            raise NotPlaying("Cannot loop because nothing is being played")
        elif len(self.music.queue[self.guild_id]) == 1 and not force:
            raise EmptyQueue("Cannot skip because queue is empty")

        current_song = self.music.queue[self.guild_id][0]
        current_song.is_looping = False
        self._previous_song = current_song
        self.voice.stop()
        try:
            new_song = self.music.queue[self.guild_id][1]
            await self.play()
            return new_song
        except IndexError:
            return current_song

    async def stop(self):
        try:
            self.music.queue[self.guild_id] = []
            self.voice.stop()
            self.music.players.remove(self)
        except ValueError:
            raise NotPlaying("Cannot loop because nothing is being played")

    async def pause(self):
        try:
            self.voice.pause()
            song = self.music.queue[self.guild_id][0]
        except IndexError:
            raise NotPlaying("Cannot pause because nothing is being played")
        return song

    async def resume(self):
        try:
            self.voice.resume()
            song = self.music.queue[self.guild_id][0]
        except (KeyError, IndexError):
            raise NotPlaying("Cannot resume because nothing is being played")
        return song

    @property
    def queue(self):
        return self.music.queue.get(self.guild_id)

    @property
    def playing(self):
        try:
            return self.music.queue[self.guild_id][0]
        except (KeyError, IndexError):
            return None

    async def toggle_song_loop(self):
        try:
            song = self.music.queue[self.guild_id][0]
        except (KeyError, IndexError):
            raise NotPlaying("Cannot loop because nothing is being played")

        song.is_looping = not song.is_looping
        return song

    async def change_volume(self, vol: int):
        self.voice.source.volume = vol
        try:
            self.music.queue[self.guild_id][0]
        except IndexError:
            raise NotPlaying("Cannot loop because nothing is being played")

    async def remove_from_queue(self, index: int):
        try:
            song = self.music.queue[self.guild_id].pop(index)
        except IndexError:
            raise NotPlaying("Cannot loop because nothing is being played")

        if index == 0:
            await self.skip(force=True)
        return song

    def delete(self):
        self.music.players.remove(self)
