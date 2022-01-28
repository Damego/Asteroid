import re
import os
from typing import Union

from discord import Member, Message, Embed, VoiceState, Guild, VoiceClient, VoiceChannel, Client, abc
from discord.ext.commands import Bot
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
import lavalink

from my_utils import AsteroidBot, NotConnectedToVoice, Cog, consts
from my_utils.functions import transform_permission


url_rx = re.compile(r'https?://(?:www\.)?.+')


class LavalinkVoiceClient(VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: Union[Client, Bot], channel: VoiceChannel):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                    'localhost',
                    2333,
                    'testpassword',
                    'us',
                    'default-node')
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_SERVER_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
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
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the 
        # disconnect
        player.channel_id = None
        self.cleanup()


class TestMusic(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = True
        self.name = 'TestMusic'

    @Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            self.bot.lavalink = lavalink.Client(self.bot.user.id)
            self.bot.lavalink.add_node('127.0.0.1', 2333, 'testpassword', 'ru', 'default-node')  # Host, Port, Password, Region, Name


    @slash_subcommand(
        base='test',
        name='play',
        description='Start playing music',
        guild_ids=consts.test_global_guilds_ids
    )
    async def play_music(self, ctx: SlashContext, *, query: str):
        await ctx.defer()
        await self._play_music(ctx, query)

    @slash_subcommand(
        base='test',
        name='stop',
        description='Stop playing music',
        guild_ids=consts.test_global_guilds_ids
    )
    async def stop_music(self, ctx: SlashContext):
        await self._stop_music(ctx)

    @slash_subcommand(
        base='test',
        name='pause',
        description='Pause playing music',
        guild_ids=consts.test_global_guilds_ids
    )
    async def pause_music(self, ctx: SlashContext):
        await self._pause_music(ctx)

    @slash_subcommand(
        base='test',
        name='resume',
        description='Resume playing music',
        guild_ids=consts.test_global_guilds_ids
    )
    async def resume_music(self, ctx: SlashContext):
        await self._resume_music(ctx)

    @slash_subcommand(
        base='test',
        name='repeat',
        description='Toggle music repeat',
        guild_ids=consts.test_global_guilds_ids
    )
    async def repeat_music(self, ctx: SlashContext):
        await self._repeat_music(ctx)

    @slash_subcommand(
        base='test',
        name='skip',
        description='Skip music',
        guild_ids=consts.test_global_guilds_ids
    )
    async def skip_music(self, ctx: SlashContext):
        await self._skip_music(ctx)

    @slash_subcommand(
        base='test',
        name='queue',
        description='Show current queue',
        guild_ids=consts.test_global_guilds_ids
    )
    async def queue_music(self, ctx: SlashContext):
        player = self.music.get_player(ctx.guild_id)
        await ctx.send(', '.join([song.name for song in player.queue]))

    async def _play_music(self, ctx: SlashContext, query: str):
        if not ctx.author.voice:
            raise NotConnectedToVoice

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
            return await ctx.send('Nothing found!')

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
        else:
            track = lavalink.models.AudioTrack(results['tracks'][0], ctx.author, recommended=True)
            player.add(requester=ctx.author, track=track)

        if not player.is_playing:
            await player.play()

        await self._send_message(ctx, track)

    async def _send_message(self, ctx, track):
        embed = self._get_music_info(ctx, track)
        return await ctx.send(embed=embed)

    def _get_music_info(self, ctx, track: lavalink.models.AudioTrack) -> Embed:
        music_requester = track.requester
        music_requester_avatar = track.requester.avatar_url
        print(dir(track))
        duration = track.duration // 1000
        if track.stream:
            duration = 'Прямая трансляция'
        else:
            duration_hours = duration // 3600
            duration_minutes = (duration // 60) % 60
            duration_seconds = duration % 60
            duration = f'{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}'

        embed = Embed(title='Играет',
                      color=self.bot.get_embed_color(ctx.guild_id))
        embed.add_field(name="Название",
                        value=f'[{track.title}]({track.uri})', inline=False)
        embed.add_field(name="Продолжительность",
                        value=duration, inline=False)
        embed.set_footer(text=f"Добавлено: {music_requester}", icon_url=music_requester_avatar)
        #embed.set_thumbnail(url=track.thumbnail)

        return embed

    async def _stop_music(self, ctx: SlashContext):
        player = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_connected:
            return await ctx.send('Not connected.', hidden=True)

        if not ctx.author.voice or ctx.author.voice.channel.id != int(
            player.channel_id
        ):
            return await ctx.send('Вы не в войсе с ботом', hidden=True)

        player.queue.clear()
        await player.stop()
        await ctx.voice_client.disconnect(force=True)
        await ctx.send('Отключено', hidden=True)

    async def _pause_music(self, ctx: SlashContext):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_connected:
            return await ctx.send('Not connected.', hidden=True)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('Вы не в войсе с ботом', hidden=True)

        if not player.is_playing:
            return await ctx.send('На паузе', hidden=True)
        await player.set_pause(True)
        await ctx.send('Музыка уже на паузе', hidden=True)


    async def _resume_music(self, ctx: SlashContext):
        player = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_connected:
            return await ctx.send('Not connected.', hidden=True)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('Вы не в войсе с ботом', hidden=True)

        if player.is_playing:
            return await ctx.send('Музыка уже играет', hidden=True)
        await player.set_pause(False)
        await ctx.send('Успешно', hidden=True)

    async def _repeat_music(self, ctx: SlashContext):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_connected:
            return await ctx.send('Not connected.', hidden=True)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('Вы не в войсе с ботом', hidden=True)

        await player.set_repeat(not player.repeat)
        await ctx.send('✔', hidden=True)

    async def _skip_music(self, ctx: SlashContext):
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild_id)
        if not player.is_connected:
            return await ctx.send('Not connected.', hidden=True)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('Вы не в войсе с ботом', hidden=True)

        try:
            new_track = await player.skip()
            await ctx.send('✔️', hidden=True)
        except Exception:
            await ctx.send('**Playlist is empty!**', delete_after=15)

def setup(bot):
    bot.add_cog(TestMusic(bot))
