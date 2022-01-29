from re import compile
from typing import Union

from discord import VoiceClient, Member, Message, Embed, VoiceState, Guild, Client, VoiceChannel
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
import lavalink

from my_utils import AsteroidBot, get_content, NotConnectedToVoice, Cog, is_enabled


url_rx = compile(r'https?://(?:www\.)?.+')


class LavalinkVoiceClient(VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    """

    def __init__(self, client, channel: VoiceChannel):
        self.client = client
        self.channel = channel

        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                'localhost',
                3678,
                'testpassword',
                'us',
                'default-node'
            )
        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
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
        self.emoji = '🎵'
        self.name = 'Music'

    @Cog.listener()
    async def on_ready(self):
        self.bot.lavalink = lavalink.Client(self.bot.user.id)
        self.bot.lavalink.add_node('127.0.0.1', 3678, 'testpassword', 'ru', 'default-node')

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.bot and member.id == self.bot.user.id and after.channel is None:
            return await self._stop_on_leave(member.guild.id)
        if (
            before.channel is not None
            and 0 < len(before.channel.members) < 2
            and before.channel.members[0].id == self.bot.user.id
        ):
            return await self._stop_on_leave(member.guild.id)

        
    @slash_subcommand(
        base='music',
        name='play',
        description='Start playing music'
    )
    @is_enabled()
    async def play_music(self, ctx: SlashContext, *, query: str):
        await ctx.defer()
        await self._play_music(ctx, query)

    @slash_subcommand(
        base='music',
        name='stop',
        description='Stop playing music'
    )
    @is_enabled()
    async def stop_music(self, ctx: SlashContext):
        await ctx.defer()
        await self._stop_music(ctx)

    @slash_subcommand(
        base='music',
        name='pause',
        description='Pause playing music'
    )
    @is_enabled()
    async def pause_music(self, ctx: SlashContext):
        await ctx.defer()
        await self._pause_music(ctx)

    @slash_subcommand(
        base='music',
        name='resume',
        description='Resume playing music'
    )
    @is_enabled()
    async def resume_music(self, ctx: SlashContext):
        await ctx.defer()
        await self._resume_music(ctx)

    @slash_subcommand(
        base='music',
        name='repeat',
        description='Toggle music repeat'
    )
    @is_enabled()
    async def repeat_music(self, ctx: SlashContext):
        await ctx.defer()
        await self._repeat_music(ctx)

    @slash_subcommand(
        base='music',
        name='skip',
        description='Skip music'
    )
    @is_enabled()
    async def skip_music(self, ctx: SlashContext):
        await ctx.defer()
        await self._skip_music(ctx)

    # * METHODS
    async def _stop_on_leave(self, guild: Guild):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(guild.id)
        if player is not None:
            player.queue.clear()
            await player.stop()
        if guild.voice_client is not None:
            await guild.voice_client.disconnect(force=True)

    async def _play_music(self, ctx: SlashContext, query: str):
        if not ctx.author.voice:
            raise NotConnectedToVoice
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('MUSIC_COMMANDS', lang)

        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if player is None:
            player = self.bot.lavalink.player_manager.create(ctx.guild_id, endpoint=str(ctx.guild.region))
        
        if not ctx.voice_client:
            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)

        if not url_rx.match(query):
            query = f'ytsearch:{query}'
        results = await player.node.get_tracks(query)
        if not results or not results['tracks']:
            return await ctx.send(content['MUSIC_NOT_FOUND_TEXT'])

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track_data in tracks:
                player.add(requester=ctx.author, track=track_data)
                await self._added_to_queue(ctx, content, tracks)
        else:
            track = lavalink.models.AudioTrack(results['tracks'][0], ctx.author, recommended=True)
            player.add(requester=ctx.author, track=results['tracks'][0])

        if not player.is_playing:
            await player.play()
        await self._send_message(ctx, track, content)

    async def _send_message(self, ctx: SlashContext, track: lavalink.AudioTrack, content: dict):
        embed = await self._get_music_info(ctx, track, content)
        await ctx.send(embed=embed)

    async def _get_music_info(self, ctx: SlashContext, track: lavalink.AudioTrack, content: dict) -> Embed:
        duration = track.duration // 1000
        if not track.stream:
            duration_hours = duration // 3600
            duration_minutes = (duration // 60) % 60
            duration_seconds = duration % 60
            duration = f'{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}'
        else:
            duration = content['LIVE_TEXT']

        embed = Embed(title=content['PLAYING_TEXT'],
                              color=self.bot.get_embed_color(ctx.guild.id))
        embed.add_field(name=content['NAME_TEXT'],
                        value=f'[{track.title}]({track.uri})', inline=False)
        embed.add_field(name=content['DURATION_TEXT'],
                        value=duration, inline=False)
        embed.set_footer(text=content['REQUESTED_BY_TEXT'].format(ctx.author.display_name), icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=f"https://i.ytimg.com/vi/{track.identifier}/maxresdefault.jpg")

        return embed

    async def __check_music_status(self, ctx: SlashContext, player: lavalink.DefaultPlayer ,content: dict):
        if not player.is_connected:
            return await ctx.send(content["BOT_NOT_CONNECTED"])
        if not ctx.author.voice or ctx.author.voice.channel.id != int(player.channel_id):
            return await ctx.send(content["NOT_CONNECTED_TO_VOICE_TEXT"])
        if not player.is_playing:
            return await ctx.send(content["NOT_PLAYING"])
        return "PASSED"


    async def _stop_music(self, ctx: SlashContext):
        player = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))
        print('passing')
        status = await self.__check_music_status(ctx, player, content)
        if status != "PASSED":
            return

        player.queue.clear()
        await player.stop()
        await ctx.voice_client.disconnect(force=True)
        await ctx.send(content["DISCONNECTED_TEXT"])

    async def _pause_music(self, ctx: SlashContext):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))

        status = await self.__check_music_status(ctx, player, content)
        if status != "PASSED":
            return

        await player.set_pause(True)
        await ctx.send(content["PAUSED_TEXT"])

    async def _resume_music(self, ctx: SlashContext):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))

        status = await self.__check_music_status(ctx, player, content)
        if status != "PASSED":
            return

        await player.set_pause(False)
        await ctx.send(content["RESUMED_TEXT"])

    async def _repeat_music(self, ctx: SlashContext,):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))

        status = await self.__check_music_status(ctx, player, content)
        if status != "PASSED":
            return

        await player.set_repeat(not player.repeat)
        if not player.repeat:
            await ctx.send(content["REPEAT_OFF_TEXT"])
        else:
            await ctx.send(content["REPEAT_ON_TEXT"])

    async def _skip_music(self, ctx: SlashContext):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        content: dict = get_content("MUSIC_COMMANDS", self.bot.get_guild_bot_lang(ctx.guild_id))

        status = await self.__check_music_status(ctx, player, content)
        if status != "PASSED":
            return

        await player.skip()
        await ctx.send(content["TRACK_SKIPPED_TEXT"])


def setup(bot):
    bot.add_cog(Music(bot))
