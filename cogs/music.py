import discord
from discord.ext import commands
import DiscordUtils
from discord import VoiceProtocol
from discord_components import Button, ButtonStyle
from discord_slash import SlashContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
)
from discord_slash_components_bridge import ComponentContext

from my_utils import AsteroidBot
from my_utils.errors import NotConnectedToVoice
from my_utils.languages import get_content
from .settings import guild_ids



class Music(commands.Cog, description='Music'):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🎵'

        self.music = DiscordUtils.Music()

        self.track_queue = {}
        self.players = {}


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            members = before.channel.members
            if len(members) == 1 and members[0].bot:
                await self.stop_on_leave(member.guild)
        #elif member.bot and after.channel is None:
        #    await self.stop_on_leave(member.guild)


    @slash_subcommand(
        base='music',
        name='play',
        description='Start playing music',
        guild_ids=guild_ids
    )
    async def play_music(self, ctx: SlashContext, *, query: str):
        await ctx.defer()
        await self._play_music(ctx, False, query)


    @slash_subcommand(
        base='music',
        name='nplay',
        description='Start playing music',
        guild_ids=guild_ids
    )
    async def button_play_music(self, ctx: SlashContext, *, query: str):
        await ctx.defer()
        await self._play_music(ctx, True, query)


    @slash_subcommand(
        base='music',
        name='stop',
        description='Stop playing music',
        guild_ids=guild_ids
    )
    async def stop_music(self, ctx: SlashContext):
        await self._stop_music(ctx)


    @slash_subcommand(
        base='music',
        name='pause',
        description='Pause playing music',
        guild_ids=guild_ids
    )
    async def pause_music(self, ctx: SlashContext):
        await self._pause_music(ctx)


    @slash_subcommand(
        base='music',
        name='resume',
        description='Resume playing music',
        guild_ids=guild_ids
    )
    async def resume_music(self, ctx: SlashContext):
        await self._resume_music(ctx)


    @slash_subcommand(
        base='music',
        name='repeat',
        description='Toggle music repeat',
        guild_ids=guild_ids
    )
    async def repeat_music(self, ctx: SlashContext):
        await self._repeat_music(ctx)


    @slash_subcommand(
        base='music',
        name='skip',
        description='Skip music',
        guild_ids=guild_ids
    )
    async def skip_music(self, ctx: SlashContext):
        await self._skip_music(ctx)




    # * METHODS
    async def stop_on_leave(self, guild: discord.Guild):
        player = self.music.get_player(guild_id=guild.id)
        voice_client: VoiceProtocol = guild.voice_client
        try:
            await player.stop()
            await voice_client.disconnect(force=True)
            button_player = self.players.get(str(guild.id))
            if button_player is not None:
                message = button_player['message']
                await message.edit(components=[])
                del self.players[str(guild.id)]
        except KeyError:
            pass


    async def _play_music(self, ctx: SlashContext, from_nplay: bool, query: str):
        if not ctx.author.voice:
            raise NotConnectedToVoice

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()
            self.track_queue[str(ctx.guild_id)] = {}

        player = self.music.get_player(guild_id=ctx.guild.id)
        if player is None:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)
        track = await player.queue(query, search=True)

        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('MUSIC_PLAY_COMMAND', lang)

        if ctx.voice_client.is_playing():
            self.track_queue[str(ctx.guild_id)][track.name] = {'track': track, 'requester_msg': ctx.author}
            return await ctx.send(content['ADDED_IN_QUEUE_TEXT'].format(track.name))

        await player.play()
        if from_nplay:
            message, components = await self._send_message(ctx, content, track, True)
            self.players[str(ctx.guild.id)] = {'message': message}
            await self._wait_button_click(ctx, content, message, components)
        else:
            await self._send_message(ctx, content, track)


    async def _wait_button_click(self, ctx, content, message, components):
        async def check(interaction):
            member: discord.Member = ctx.guild.get_member(interaction.author_id)
            if member.guild_permissions.move_members:
                return True

            if member.voice is None:
                return False
            channel = member.voice.channel
            if channel is None:
                return False

            members = member.voice.channel.members
            for member in members:
                if member.id == 833349109347778591:
                    return True


        while True:
            interaction: ComponentContext = await self.bot.wait_for("button_click", check=lambda inter: inter.message.id == message.id)
            is_in_channel = await check(interaction)
            if not is_in_channel:
                await interaction.send(content=content['NOT_CONNECTED_TO_VOICE'])
                continue
            await interaction.defer(edit_origin=True)

            button_id = interaction.custom_id
            try:
                if button_id == 'pause':
                    await self._pause_music(ctx, content=content, from_button=True, message=message, components=components)
                elif button_id == 'stop':
                    await self._stop_music(ctx, from_button=True, message=message)
                    del self.players[str(ctx.guild_id)]
                    del self.track_queue[str(ctx.guild_id)]
                    return
                elif button_id == 'skip':
                    await self._skip_music(ctx, from_button=True, message=message)
                elif button_id == 'resume':
                    await self._resume_music(ctx, content=content, from_button=True, message=message, components=components)
                elif button_id == 'toggle_loop':
                    await self._repeat_music(ctx, content, from_button=True, message=message, components=components)
            except Exception as e:
                print(e)


    async def _send_message(self, ctx, content, track, from_nplay:bool=False):
        embed = self._get_music_info(ctx, content, track)

        if from_nplay:
            components = [
                [
                    Button(style=ButtonStyle.gray, label=content['PAUSE_BUTTON'], id='pause'),
                    Button(style=ButtonStyle.red, label=content['STOP_BUTTON'], id='stop'),
                    Button(style=ButtonStyle.blue, label=content['SKIP_BUTTON'], id='skip'),
                    Button(style=ButtonStyle.blue, label=content['TOGGLE_OFF_BUTTON'], id='toggle_loop')
                ]
            ]

            message = await ctx.send(embed=embed, components=components)
            return message, components
        return await ctx.send(embed=embed)


    async def _update_msg(self, ctx, message, track):
        music_requester = self.track_queue[str(ctx.guild_id)].get(track.name)["requester_msg"]
        embed = self._get_music_info(ctx, track, music_requester=music_requester)
        await message.edit(embed=embed)


    def _get_music_info(self, ctx, content, track, music_requester=None) -> discord.Embed:
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
            duration = content['LIVE_TEXT']

        embed = discord.Embed(title=content['PLAYING_TEXT'],
                              color=self.bot.get_embed_color(ctx.guild.id))
        embed.add_field(name=content['NAME_TEXT'],
                        value=f'[{track.name}]({track.url})', inline=False)
        embed.add_field(name=content['DURATION_TEXT'],
                        value=duration, inline=False)
        embed.set_footer(text=content['WHO_ADDED_TEXT'].format(music_requester), icon_url=music_requester_avatar)
        embed.set_thumbnail(url=track.thumbnail)

        return embed


    async def _stop_music(self, ctx: SlashContext, *, from_button:bool=False, message:discord.Message=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if ctx.voice_client.is_playing():
            await player.stop()
            await ctx.voice_client.disconnect()
        if from_button:
            await message.edit(components=[])
        else:
            await ctx.send('✔️', hidden=True)

    async def _pause_music(self, ctx: SlashContext, *, content=None, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if ctx.voice_client.is_playing():
            await player.pause()
            if from_button:
                try:
                    components[0][0] = Button(
                        style=ButtonStyle.green, label=content['RESUME_BUTTON'], id='resume')
                    await message.edit(components=components)
                except Exception as e:
                    print('IN PAUSE', e)
            else:
                await ctx.send('✔️', hidden=True)
        else:
            embed = discord.Embed(title='Music not playing!', color=self.bot.get_embed_color(ctx.guild.id))
            await ctx.send(embed=embed, delete_after=10)

    async def _resume_music(self, ctx: SlashContext, *, content=None, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if not ctx.voice_client.is_playing():
            await player.resume()
            if from_button:
                components[0][0] = Button(
                    style=ButtonStyle.gray, label=content['PAUSE_BUTTON'], id='pause')
                await message.edit(components=components)
            else:
                await ctx.send('✔️', hidden=True)

    async def _repeat_music(self, ctx: SlashContext, content, *, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        song = await player.toggle_song_loop()

        if not from_button:
            return await ctx.send('✔️', hidden=True)

        label = content['TOGGLE_OFF_BUTTON'] if song.is_looping else content['TOGGLE_ON_BUTTON']
        components[0][3] = Button(
                style=ButtonStyle.blue,
                label=label,
                id='toggle_loop'
        )
        await message.edit(components=components)


    async def _skip_music(self, ctx: SlashContext, *, from_button:bool=False, message:discord.Message=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        try:
            new_track = await player.skip(force=True)
            if not from_button:
                return await ctx.send('✔️', hidden=True)
            await self._update_msg(ctx, message, new_track)
        except Exception:
            await ctx.send('**Playlist is empty!**', delete_after=15)


    @slash_command(
        name='test',
        guild_ids=guild_ids
    )
    async def test_command(self, ctx: SlashContext):
        await ctx.send('hi!')



def setup(bot):
    bot.add_cog(Music(bot))
