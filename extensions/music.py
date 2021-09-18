import discord
from discord.ext import commands
import DiscordUtils
from discord_components import Button, ButtonStyle


class NotConnectedToVoice(commands.CommandError):
    pass


class Music(commands.Cog, description='Music'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🎵'

        self.music = DiscordUtils.Music()

        self.track_dict = {}


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            members = before.channel.members
            if len(members) == 1 and members[0].bot:
                await self.stop_on_leave(member.guild)
        elif member.bot and after.channel is None and before.channel:
            members = before.channel.members
            if len(members) == 0: return
            await self.stop_on_leave(member.guild)


    @commands.command(name='play', description='Start playing music', help='[url || video name]')
    async def play_music(self, ctx, *, query):
        await self._play_music(ctx, False, query)


    @commands.command(name='nplay', description='Start playing music with button', help='[url || video name]')
    async def button_play_music(self, ctx, *, query):
        await self._play_music(ctx, True, query)


    @commands.command(name='stop', description='Stop playing music', help=' ')
    async def stop_music(self, ctx:commands.Context):
        await self._stop_music(ctx)


    @commands.command(name='pause', aliases=['fp'], description='Pause playing music', help=' ')
    async def pause_music(self, ctx:commands.Context):
        await self._pause_music(ctx)


    @commands.command(name='resume', aliases=['fr'], description='Resume playing music', help=' ')
    async def resume_music(self, ctx:commands.Context):
        await self._resume_music(ctx)


    @commands.command(name='repeat', description='Toggle music repeat', help=' ')
    async def repeat_music(self, ctx:commands.Context):
        await self._repeat_music(ctx)


    @commands.command(name='skip', aliases=['fs'], description='Skip music', help=' ')
    async def skip_music(self, ctx:commands.Context):
        await self._skip_music(ctx)




    # * METHODS
    async def stop_on_leave(self, guild: discord.Guild):
        player = self.music.get_player(guild_id=guild.id)
        voice_client = guild.voice_client
        try:
            await player.stop()
            await voice_client.disconnect()
        except Exception as e:
            print('stop_on_leave error: ', e)


    async def _play_music(self, ctx:commands.Context, from_nplay:bool, query:str):
        if not ctx.message.author.voice:
            raise NotConnectedToVoice

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()

        player = self.music.get_player(guild_id=ctx.guild.id)
        if player is None:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)
        track = await player.queue(query, search=True)

        if ctx.voice_client.is_playing():
            self.track_dict[track.name] = {'track': track, 'requester_msg': ctx.author}
            return await ctx.send(f"`{track.name}` was added in queue")

        await player.play()
        if from_nplay:
            message, components = await self._send_message(ctx, track, True)
            await self._wait_button_click(ctx, message, components)
        else:
            await self._send_message(ctx, track)


    async def _wait_button_click(self, ctx, message, components):
        async def check(interaction):
            member: discord.Member = ctx.guild.get_member(interaction.user.id)
            if member.guild_permissions.move_members:
                return True

            if member.voice is None:
                return False
            channel = member.voice.channel
            if channel is None:
                return False

            members = member.voice.channel.members
            for member in members:
                if member.id == '833349109347778591':
                    return True


        while True:
            interaction = await self.bot.wait_for("button_click")
            is_in_channel = await check(interaction)
            if not is_in_channel:
                await interaction.send(content='Connect to voice channel with a bot')
                continue
            await interaction.respond(type=6)

            button_id = interaction.component.id
            try:
                if button_id == 'pause':
                    await self._pause_music(ctx, from_button=True, message=message, components=components)
                elif button_id == 'stop':
                    return await self._stop_music(ctx, from_button=True, message=message)
                elif button_id == 'skip':
                    await self._skip_music(ctx, from_button=True, message=message)
                elif button_id == 'resume':
                    await self._resume_music(ctx, from_button=True, message=message, components=components)
                elif button_id == 'toggle_loop':
                    await self._repeat_music(ctx, from_button=True, message=message, components=components)
            except Exception as e:
                print(e)


    async def _send_message(self, ctx, track, from_nplay:bool=False):
        embed = self._get_music_info(ctx, track)

        if from_nplay:
            components = [[
                Button(style=ButtonStyle.gray, label='Pause', id='pause'),
                Button(style=ButtonStyle.red, label='Stop', id='stop'),
                Button(style=ButtonStyle.blue, label='Skip', id='skip'),
                Button(style=ButtonStyle.blue, label='Enable repeat', id='toggle_loop')
            ]]

            message = await ctx.send(embed=embed, components=components)
            return message, components
        return await ctx.send(embed=embed)


    async def _update_msg(self, ctx, message, track):
        music_requester = self.track_dict.get(track.name)["requester_msg"]
        embed = self._get_music_info(ctx, track, music_requester=music_requester)
        await message.edit(embed=embed)


    async def _get_music_info(self, ctx, track, music_requester=None) -> discord.Embed:
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
            duration = 'Live'

        embed = discord.Embed(title='Playing',
                              color=self.bot.get_embed_color(ctx.guild.id))
        embed.add_field(name='Name:',
                        value=f'[{track.name}]({track.url})', inline=False)
        embed.add_field(name='Duration:',
                        value=duration, inline=False)
        embed.set_footer(text=f'Added: {music_requester}', icon_url=music_requester_avatar)
        embed.set_thumbnail(url=track.thumbnail)

        return embed


    async def _stop_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if ctx.voice_client.is_playing():
            await player.stop()
            await ctx.voice_client.disconnect()
        if from_button:
            await message.edit(components=[])
        else:
            await ctx.message.add_reaction('✅')

    async def _pause_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if ctx.voice_client.is_playing():
            await player.pause()
            if from_button:
                try:
                    components[0][0] = Button(
                        style=ButtonStyle.green, label='Resume', id='resume')
                    await message.edit(components=components)
                except Exception as e:
                    print('IN PAUSE', e)
            else:
                await ctx.message.add_reaction('✅')
        else:
            embed = discord.Embed(title='Music not playing!', color=self.bot.get_embed_color(ctx.guild.id))
            await ctx.send(embed=embed, delete_after=10)

    async def _resume_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if not ctx.voice_client.is_playing():
            await player.resume()
            if from_button:
                components[0][0] = Button(
                    style=ButtonStyle.gray, label='Pause', id='pause')
                await message.edit(components=components)
            else:
                await ctx.message.add_reaction('✅')

    async def _repeat_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        song = await player.toggle_song_loop()

        if not from_button:
            return await ctx.message.add_reaction('✅')

        label = 'Disable repeat' if song.is_looping else 'Enable repeat'
        components[0][3] = Button(
                style=ButtonStyle.blue,
                label=label,
                id='toggle_loop'
        )
        await message.edit(components=components)


    async def _skip_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        try:
            new_track = await player.skip(force=True)
            if not from_button:
                return await ctx.message.add_reaction('✅')
            await self._update_msg(ctx, message, new_track)
        except Exception:
            await ctx.send('**Playlist is empty!**', delete_after=15)



def setup(bot):
    bot.add_cog(Music(bot))
