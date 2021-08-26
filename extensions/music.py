import discord
from discord.ext import commands
import DiscordUtils
from discord_components import Button, ButtonStyle


class NotConnectedToVoice(commands.CommandError):
    pass


class Music(commands.Cog, description='Музыка без плеера'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.music = DiscordUtils.Music()

        self.track_dict = {}


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            members = before.channel.members
            if len(members) == 1 and members[0].bot:
                await self.stop_on_leave(member.guild.id)
                system_channel = member.guild.system_channel
                if system_channel:
                    await system_channel.send('**Бот отключился, из-за отсутствия слушателей!**', delete_after=10)
        elif member.bot and after.channel is None and before.channel:
            members = before.channel.members
            if len(members) == 0: return
            await self.stop_on_leave(member.guild.id)


    @commands.command(name='play', description='Запускает музыку', help='[ссылка || название видео]')
    async def play_music(self, ctx, *, query):
        await self._play_music(ctx, False, query)


    @commands.command(name='nplay', description='Запускает музыку', help='[ссылка || название видео]')
    async def button_play_music(self, ctx, *, query):
        await self._play_music(ctx, True, query)


    @commands.command(name='stop', description='Останавливает произведение музыку', help=' ')
    async def stop_music(self, ctx:commands.Context):
        await self._stop_music(ctx)


    @commands.command(name='pause', aliases=['fp'], description='Ставит музыку на паузу', help=' ')
    async def pause_music(self, ctx:commands.Context):
        await self._pause_music(ctx)


    @commands.command(name='resume', aliases=['fr'], description='Снимает паузу с музыки', help=' ')
    async def resume_music(self, ctx:commands.Context):
        await self._resume_music(ctx)


    @commands.command(name='repeat', description='Включает/Выключает повтор музыки', help=' ')
    async def repeat_music(self, ctx:commands.Context):
        await self._repeat_music(ctx)


    @commands.command(name='skip', aliases=['fs'], description='Пропускает музыку', help=' ')
    async def skip_music(self, ctx:commands.Context):
        await self._skip_music(ctx)




    # * METHODS
    async def stop_on_leave(self, guild_id):
        player = self.music.get_player(guild_id=guild_id)
        voice_client = self.bot.get_guild(guild_id)
        try:
            await player.stop()
            await voice_client.disconnect()
        except Exception:
            pass


    async def _play_music(self, ctx:commands.Context, from_nplay:bool, query:str):
        await ctx.message.delete()
        if not ctx.message.author.voice:
            raise NotConnectedToVoice

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()

        player = self.music.get_player(guild_id=ctx.guild.id)
        if player is None:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)
        track = await player.queue(query, search=True)

        if not ctx.voice_client.is_playing():
            await player.play()
            if from_nplay:
                message, components = await self._send_message(ctx, track, True)
                await self._wait_button_click(ctx, message, components)
            else:
                await self._send_message(ctx, track)
        else:
            await ctx.send(f"`{track.name}` был добавлен в очередь")
            self.track_dict[track.name] = {'track': track, 'requester_msg': ctx.author}


    async def _wait_button_click(self, ctx, message, components):
        async def check(interaction):
            member = ctx.guild.get_member(interaction.user.id)
            if ('move_members', True) in member.guild_permissions:
                return True

            channel = member.voice.channel
            if not channel:
                return False

            members = member.voice.channel.members
            for member in members:
                if member.bot:
                    return True

        while True:
            interaction = await self.bot.wait_for("button_click")
            is_in_channel = await check(interaction)
            if not is_in_channel:
                await interaction.respond(type=5, content='Подключитесь к каналу, для управления музыкой')
            else:
                await interaction.respond(type=6)
                button_id = interaction.component.id
                
                try:
                    if button_id == 'pause':
                        await self._pause_music(ctx, True, message, components)
                    elif button_id == 'stop':
                        return await self._stop_music(ctx, True, message)
                    elif button_id == 'skip':
                        await self._skip_music(ctx, True, message)
                    elif button_id == 'resume':
                        await self._resume_music(ctx, True, message, components)
                    elif button_id == 'toggle_loop':
                        await self._repeat_music(ctx, True, message, components)
                except Exception as e:
                    print(e)


    async def _send_message(self, ctx, track, *, from_nplay:bool=False):
        duration = track.duration
        if duration != 0.0:
            duration_hours = duration // 3600
            duration_minutes = (duration // 60) % 60
            duration_seconds = duration % 60
            duration = f'{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}'
        else:
            duration = 'Прямая трансляция'

        embed = discord.Embed(title='Запуск музыки',
                            color=self.bot.get_embed_color(ctx.guild.id))
        embed.add_field(name='Название:',
                        value=f'[{track.name}]({track.url})', inline=False)
        embed.add_field(name='Продолжительность:',
                        value=duration, inline=False)
        embed.set_footer(text=f'Добавлено: {ctx.message.author}', icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=track.thumbnail)

        if from_nplay:
            components = [[
                Button(style=ButtonStyle.gray, label='Пауза', id='pause'),
                Button(style=ButtonStyle.red, label='Стоп', id='stop'),
                Button(style=ButtonStyle.blue, label='Пропустить', id='skip'),
                Button(style=ButtonStyle.blue, label='Вкл. повтор', id='toggle_loop')
            ]]

            message:discord.Message = await ctx.send(embed=embed, components=self.components)
            return message, components
        return await ctx.send(embed=embed)

    async def _update_msg(self, ctx, message, track):
        music_requester = self.track_dict.get(track.name)["requester_msg"]
        music_requester_avatar = music_requester.avatar_url
        duration = track.duration
        if duration != 0.0:
            duration_hours = duration // 3600
            duration_minutes = (duration // 60) % 60
            duration_seconds = duration % 60
            duration = f'{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}'
        else:
            duration = 'Прямая трансляция'

        embed = discord.Embed(title='Запуск музыки',
                              color=self.bot.get_embed_color(ctx.guild.id))
        embed.add_field(name='Название:',
                        value=f'[{track.name}]({track.url})', inline=False)
        embed.add_field(name='Продолжительность:',
                        value=duration, inline=False)
        embed.set_footer(text=f'Добавлено: {music_requester}', icon_url=music_requester_avatar)
        embed.set_thumbnail(url=track.thumbnail)

        await message.edit(embed=embed)


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
                        style=ButtonStyle.green, label='Продолжить', id='resume')
                    await message.edit(components=components)
                except Exception as e:
                    print('IN PAUSE', e)
            else:
                await ctx.message.add_reaction('✅')
        else:
            embed = discord.Embed(title='Музыка не воспроизводится!', color=self.bot.get_embed_color(ctx.guild.id))
            await ctx.send(embed=embed, delete_after=10)

    async def _resume_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        if not ctx.voice_client.is_playing():
            await player.resume()
            if from_button:
                self.components[0][0] = Button(
                    style=ButtonStyle.gray, label='Пауза', id=1)
                await message.edit(components=components)
            else:
                await ctx.message.add_reaction('✅')

    async def _repeat_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None, components:list=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        song = await player.toggle_song_loop()

        if not from_button:
            return await ctx.message.add_reaction('✅')

        if song.is_looping:
            components[0][3] = Button(
                style=ButtonStyle.blue, label='Выкл. повтор', id='toggle_loop')
        else:
            components[0][3] = Button(
                style=ButtonStyle.blue, label='Вкл. повтор', id='toggle_loop')
        await message.edit(components=components)


    async def _skip_music(self, ctx:commands.Context, *, from_button:bool=False, message:discord.Message=None):
        player = self.music.get_player(guild_id=ctx.guild.id)
        try:
            new_track = await player.skip(force=True)
            if not from_button:
                return await ctx.message.add_reaction('✅')
            await self._update_message(ctx, message, new_track)
        except Exception:
            await ctx.send('**Плейлист пуст! Добавьте музыку!**', delete_after=15)



def setup(bot):
    bot.add_cog(Music(bot))
