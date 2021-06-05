import os

import discord
from discord.ext import commands
from replit import Database, db
from discord_components import DiscordComponents, Button, ButtonStyle
import lavalink

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

class Music(commands.Cog, description='Музыка'):
    def __init__(self,bot):
        self.bot = bot
        self.hidden = False

        self.bot.music = lavalink.Client(self.bot.user.id)
        self.bot.music.add_node('localhost', 7000, 'testing', 'eu', 'music-node')
        self.bot.add_listener(self.bot.music.voice_update_handler, 'on_socket_response')
        self.bot.music.add_event_hook(self.track_hook)

        self.track_dict = {}

    async def track_hook(self, event):
        #if isinstance(event, lavalink.events.QueueEndEvent):
        #    guild_id = int(event.player.guild_id)
        #    await self.connect_to(guild_id, None)
        if isinstance(event, lavalink.TrackStartEvent):
            await self.update_message(event.track['title'])

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.connect_to(member.guild.id, None)
                await self.msg.edit(components=[])
                await self.msg.channel.send('**Бот отключился, из-за отсутствия слушателей!**', delete_after=10)


    async def connect_to(self, guild_id: int, channel_id: str):
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    async def track_parse(self, track):
        title = track['info']['title']
        uri = track['info']['uri']

        if not track['info']['isStream']:
            duration = int(track['info']['length']) // 1000
            dur_hours = duration // 3600
            dur_min = (duration // 60) % 60
            dur_sec = duration % 60
            lenght = f'{dur_hours:02}:{dur_min:02}:{dur_sec:02}'
        else:
            lenght = 'Прямая трансляция'

        video_id = uri.split('=')[1]

        video_thumbnail = f'https://img.youtube.com/vi/{video_id}/0.jpg'
        return title, uri, lenght, video_thumbnail

    async def get_player(self, obj):
        if isinstance(obj, commands.Context):
            guild_id = obj.guild.id
        elif isinstance(obj, discord.Guild):
            guild_id = obj.id
            
        player = self.bot.music.player_manager.get(guild_id)
        if player is None:
            player = self.bot.music.player_manager.create(guild_id, endpoint='russia')
        return player

    def check(self, ctx):
        if ctx.author.voice in ctx.bot.voice_clients:
            return True

    async def wait_button_click(self, ctx, msg, track):
        while True:
            res = await self.bot.wait_for("button_click", check=self.check(ctx))
            await res.respond(type=6)
            id = res.component.id

            if id == '1':
                await self.pause(ctx, msg)
            elif id == '2':
                await self.stop(ctx, msg)
                return
            elif id == '3':
                await self.skip(ctx, msg)
            elif id == '4':
                await self.resume(ctx, msg)
            elif id == '5':
                await self.repeat(ctx, track)
            

    async def send_msg(self, ctx, track):
        title, uri, lenght, video_thumbnail = await self.track_parse(track)
        embed = discord.Embed(title='Запуск музыки', color=get_embed_color(ctx.message))
        embed.add_field(name='Название:', value=f'[{title}]({uri})', inline=False)
        embed.add_field(name='Продолжительность:',value=lenght, inline=False)
        embed.set_footer(text=f'Добавлено: {ctx.message.author}',icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=video_thumbnail)

        components = [[
            Button(style=ButtonStyle.gray, label='Пауза', id=1),
            Button(style=ButtonStyle.red, label='Стоп', id=2),
            Button(style=ButtonStyle.blue, label='Пропустить', id=3),
            Button(style=ButtonStyle.blue, label='Повтор', id=5)
        ]]

        await ctx.message.delete()
        msg = await ctx.send(embed=embed,
        components=components)
        self.msg = msg
        return msg

    async def update_message(self, track):
        try:
            track_info = self.track_dict.get(track)
            track = track_info['track']
            track_requester_msg = track_info['requester_msg']
            title, uri, lenght, video_thumbnail = await self.track_parse(track)
        except:
            return

        embed = discord.Embed(title='Запуск музыки', color=get_embed_color(track_requester_msg))
        embed.add_field(name='Название:', value=f'[{title}]({uri})', inline=False)
        embed.add_field(name='Продолжительность:',value=lenght, inline=False)
        embed.set_footer(text=f'Добавлено: {track_requester_msg.author}',icon_url=track_requester_msg.author.avatar_url)
        embed.set_thumbnail(url=video_thumbnail)
        await self.msg.edit(embed=embed)


    @commands.command(name='play', aliases=['музыка','играть','муз','м'], description='Запускает музыку', help='[ссылка || название видео]')
    async def play_music(self, ctx, *, query):
        if not ctx.message.author.voice:
            raise NotConnectedToVoice
        
        player = await self.get_player(ctx)
        voice_channel = ctx.message.author.voice.channel
        self.author_of_query = ctx.message.author

        if not player.is_connected:
            player.store('channel', ctx.channel.id)
            await self.connect_to(ctx.guild.id, str(voice_channel.id))

        if query.startswith('https') or query.startswith('youtube'):
            result = query
        else:
            result = f'ytsearch: {query}'

        results = await player.node.get_tracks(result)
        track = results['tracks'][0]
        
        if not player.is_playing:
            self.author_of_query = ctx.message
            player.add(requester=ctx.author.id, track=track)
            await player.play()
            msg = await self.send_msg(ctx, track)
            await self.wait_button_click(ctx, msg, track)
        else:
            player.add(requester=ctx.author.id, track=track)
            await ctx.message.delete()
            await ctx.send(f"`{track['info']['title']}` был добавлен в очередь")
            self.track_dict[track['info']['title']] = {'track':track, 'requester_msg':ctx.message}
        

    async def stop(self, ctx, msg):
        player = await self.get_player(ctx)
        if player.is_playing:
            await player.stop()
            await self.connect_to(ctx.guild.id, None)
        return await msg.edit(components=[])

    async def pause(self, ctx, msg):
        player = await self.get_player(ctx)
        if player.is_playing:
            await player.set_pause(True)

            await msg.edit(components=[[
                Button(style=ButtonStyle.green, label='Продолжить', id=4),
                Button(style=ButtonStyle.red, label='Стоп', id=2),
                Button(style=ButtonStyle.blue, label='Пропустить', id=3),
                Button(style=ButtonStyle.blue, label='Повтор', id=5)
            ]])
        else:
            embed = discord.Embed(title='Музыка не воспроизводится!', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed, delete_after=10)


    async def resume(self, ctx, msg):
        player = await self.get_player(ctx)
        await player.set_pause(False)

        await msg.edit(components=[[
            Button(style=ButtonStyle.gray, label='Пауза', id=1), 
            Button(style=ButtonStyle.red, label='Стоп', id=2), 
            Button(style=ButtonStyle.blue, label='Пропустить', id=3), 
            Button(style=ButtonStyle.blue, label='Повтор', id=5)
        ]])

    async def repeat(self, ctx, track):
        player = await self.get_player(ctx)
        player.add(requester=ctx.author.id, track=track)
        await player.play()

    async def skip(self, ctx, msg):
        player = await self.get_player(ctx)
        await player.skip()

    # ERRORS
    @play_music.error
    async def play_music_error(self, ctx, error):
        if isinstance(error, NotConnectedToVoice):
            await ctx.send('Вы не подключены к голосовому чату!')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, lavalink.NodeException):
            await ctx.send('Не удаётся подключится к серверу')


def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Music(bot))