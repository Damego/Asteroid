from discord import Member, Message, Embed, VoiceState, Guild, VoiceClient
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand

from my_utils import AsteroidBot, NotConnectedToVoice, Cog
from my_utils.music import Music
from .settings import guild_ids


class NewMusic(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.name = 'NewMusic'
        self.music = Music(bot)
        self.track_queue = {}
        self.players = {}

    @Cog.listener()
    async def on_music_error(self, previous_song, current_song):
        print('MY EVENT')
        print(previous_song)
        print(current_song)

    @slash_subcommand(
        base='test',
        name='play',
        description='Start playing music',
        guild_ids=guild_ids
    )
    async def play_music(self, ctx: SlashContext, *, query: str):
        await ctx.defer()
        await self._play_music(ctx, query)

    @slash_subcommand(
        base='test',
        name='stop',
        description='Stop playing music',
        guild_ids=guild_ids
    )
    async def stop_music(self, ctx: SlashContext):
        await self._stop_music(ctx)

    @slash_subcommand(
        base='test',
        name='pause',
        description='Pause playing music',
        guild_ids=guild_ids
    )
    async def pause_music(self, ctx: SlashContext):
        await self._pause_music(ctx)

    @slash_subcommand(
        base='test',
        name='resume',
        description='Resume playing music',
        guild_ids=guild_ids
    )
    async def resume_music(self, ctx: SlashContext):
        await self._resume_music(ctx)

    @slash_subcommand(
        base='test',
        name='repeat',
        description='Toggle music repeat',
        guild_ids=guild_ids
    )
    async def repeat_music(self, ctx: SlashContext):
        await self._repeat_music(ctx)

    @slash_subcommand(
        base='test',
        name='skip',
        description='Skip music',
        guild_ids=guild_ids
    )
    async def skip_music(self, ctx: SlashContext):
        await self._skip_music(ctx)

    @slash_subcommand(
        base='test',
        name='queue',
        description='Show current queue',
        guild_ids=guild_ids
    )
    async def queue_music(self, ctx: SlashContext):
        player = self.music.get_player(ctx.guild_id)
        await ctx.send(', '.join([song.name for song in player.queue]))

    async def _play_music(self, ctx: SlashContext, query: str):
        if not ctx.author.voice:
            raise NotConnectedToVoice

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()

        player = self.music.get_player(guild_id=ctx.guild_id)
        if player is None:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)
        track = await player.add_to_queue(query, search=True)

        if ctx.voice_client.is_playing():
            if ctx.guild_id not in self.track_queue:
                self.track_queue[ctx.guild_id] = {}
            self.track_queue[ctx.guild_id][track.name] = {'track': track, 'requester_msg': ctx.author}
            return await ctx.send(f'ДОБАВЛЕНО: \n`{track.name}`')

        await player.play()
        await self._send_message(ctx, track)

    async def _send_message(self, ctx, track):
        embed = self._get_music_info(ctx, track)
        return await ctx.send(embed=embed)

    def _get_music_info(self, ctx, track, music_requester=None) -> Embed:
        if music_requester is None:
            music_requester = ctx.author
            music_requester_avatar = ctx.author.avatar_url
        else:
            music_requester_avatar = music_requester.avatar_url

        duration = track.duration
        if duration != 0.0:
            duration_hours = duration // 3600
            duration_minutes = (duration // 60) % 60
            duration_seconds = duration % 60
            duration = f'{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}'
        else:
            duration = 'Прямая трансляция'

        embed = Embed(title='Играет',
                      color=self.bot.get_embed_color(ctx.guild_id))
        embed.add_field(name="Название",
                        value=f'[{track.name}]({track.url})', inline=False)
        embed.add_field(name="Продолжительность",
                        value=duration, inline=False)
        embed.set_footer(text=f"Добавлено: {music_requester}", icon_url=music_requester_avatar)
        embed.set_thumbnail(url=track.thumbnail)

        return embed

    async def _stop_music(self, ctx: SlashContext):
        player = self.music.get_player(guild_id=ctx.guild_id)
        if ctx.voice_client.is_playing():
            await player.stop()
            await ctx.voice_client.disconnect(force=True)
            await ctx.send('Отключено', hidden=True)

    async def _pause_music(self, ctx: SlashContext):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if ctx.voice_client.is_playing():
            await player.pause()
            await ctx.send('✔️', hidden=True)
        else:
            embed = Embed(title='Music not playing!', color=self.bot.get_embed_color(ctx.guild.id))
            await ctx.send(embed=embed, delete_after=10)

    async def _resume_music(self, ctx: SlashContext):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if not ctx.voice_client.is_playing():
            await player.resume()
            await ctx.send('✔️', hidden=True)

    async def _repeat_music(self, ctx: SlashContext):
        player = self.music.get_player(guild_id=ctx.guild.id)
        await player.toggle_song_loop()
        await ctx.send('✔', hidden=True)

    async def _skip_music(self, ctx: SlashContext):
        player = self.music.get_player(guild_id=ctx.guild.id)
        try:
            new_track = await player.skip(force=True)
            await ctx.send('✔️', hidden=True)
        except Exception:
            await ctx.send('**Playlist is empty!**', delete_after=15)

def setup(bot):
    bot.add_cog(NewMusic(bot))
