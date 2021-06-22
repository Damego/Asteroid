import os

import discord
from discord.ext import commands
from replit import Database, db
import DiscordUtils

if db is not None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)


def get_embed_color(message):
    """Get color for embeds from json """
    return int(server[str(message.guild.id)]['embed_color'], 16)


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
            if not [m for m in before.channel.members if not m.bot]:
                await self.voice_client.disconnect()
                await self.msg.edit(components=[])
                await self.msg.channel.send('**Бот отключился, из-за отсутствия слушателей!**', delete_after=10)

    
    async def send_msg(self, ctx, track):
        duration = track.duration
        if duration != 0.0:
            duration_hours = duration // 3600
            duration_minutes = (duration // 60) % 60
            duration_seconds = duration % 60
            duration = f'{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}'
        else:
            duration = 'Прямая трансляция'

        embed = discord.Embed(title='Запуск музыки',
                            color=get_embed_color(ctx.message))
        embed.add_field(name='Название:',
                        value=f'[{track.name}]({track.url})', inline=False)
        embed.add_field(name='Продолжительность:',
                        value=duration, inline=False)
        embed.set_footer(text=f'Добавлено: {ctx.message.author}', icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=track.thumbnail)


        msg = await ctx.send(embed=embed)
        self.msg = msg
        return msg

    @commands.command(name='play', description='Запускает музыку', help='[ссылка || название видео]')
    async def play_music(self, ctx, *, query):
        if not ctx.message.author.voice:
            raise NotConnectedToVoice

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()
            self.voice_client = ctx.voice_client

        player = self.music.get_player(guild_id=ctx.guild.id)
        if player is None:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)

        track = await player.queue(query, search=True)
        await ctx.message.delete()
        if not ctx.voice_client.is_playing():
            await player.play()
            await self.send_msg(ctx, track)
        else:
            await ctx.send(f"`{track.name}` был добавлен в очередь")
            self.track_dict[track.name] = {'track': track, 'requester_msg': ctx.author}


    @commands.command(name='stop', description='Останавливает произведение музыку', help=' ')
    async def stop_music(self, ctx):
        player = self.music.get_player(guild_id=ctx.guild.id)
        try:
            if ctx.voice_client.is_playing():
                try:
                    await player.stop()
                except Exception:
                    pass
            await ctx.voice_client.disconnect()
            await ctx.message.add_reaction('✅')
        except Exception:
            await ctx.message.add_reaction('❌')
        

    @commands.command(name='pause', aliases=['fp'], description='Ставит музыку на паузу', help=' ')
    async def pause_music(self, ctx):
        try:
            player = self.music.get_player(guild_id=ctx.guild.id)
            if ctx.voice_client.is_playing():
                await player.pause()
                await ctx.message.add_reaction('✅')
                return
        except Exception:
            await ctx.message.add_reaction('❌')

    @commands.command(name='resume', aliases=['fr'], description='Снимает паузу с музыки', help=' ')
    async def resume_music(self, ctx):
        try:
            player = self.music.get_player(guild_id=ctx.guild.id)
            if not ctx.voice_client.is_playing():
                await player.resume()
                await ctx.message.add_reaction('✅')
                return
        except Exception:
            await ctx.message.add_reaction('❌')


    @commands.command(name='repeat', description='Включает/Выключает повтор музыки', help=' ')
    async def repeat_music(self, ctx):
        try:
            player = self.music.get_player(guild_id=ctx.guild.id)
            await player.toggle_song_loop()
            await ctx.message.add_reaction('✅')
        except Exception:
            await ctx.message.add_reaction('❌')


    @commands.command(name='skip', aliases=['fs'], description='Пропускает музыку', help=' ')
    async def skip_music(self, ctx):
        try:
            player = self.music.get_player(guild_id=ctx.guild.id)
            try:
                old_track, new_track = await player.skip(force=True)
            except TypeError:
                await ctx.send('**Плейлист пуст! Добавьте музыку!**', delete_after=15)
            return await ctx.message.add_reaction('✅')
        except Exception:
            await ctx.message.add_reaction('❌')

    # ERRORS
    @play_music.error
    async def play_music_error(self, ctx, error):
        if isinstance(error, NotConnectedToVoice):
            await ctx.send('Вы не подключены к голосовому чату!')


def setup(bot):
    bot.add_cog(Music(bot))
