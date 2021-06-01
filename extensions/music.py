import os
from time import time

import discord
from discord.ext import commands
from replit import Database, db
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


class Music(commands.Cog, description='Музыка'):
    def __init__(self,bot):
        self.bot = bot
        self.hidden = False

        self.bot.music = lavalink.Client(self.bot.user.id)
        self.bot.music.add_node('localhost', 7000, 'testing', 'eu', 'music-node')
        self.bot.add_listener(self.bot.music.voice_update_handler, 'on_socket_response')
        self.bot.music.add_event_hook(self.track_hook)

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)
      
    async def connect_to(self, guild_id: int, channel_id: str):
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    @commands.command(name='play', aliases=['музыка','играть','муз','м'], description='Запускает музыку', help='[ссылка || название видео]')
    async def play_music(self, ctx, *, query):
        if ctx.message.author.voice:
            self.vc = ctx.message.author.voice.channel
            self.author_of_query = ctx.message.author

            player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
            if not player.is_connected:
                player.store('channel', ctx.channel.id)
                await self.connect_to(ctx.guild.id, str(self.vc.id))

            self.player = self.bot.music.player_manager.get(ctx.guild.id)

            if query.startswith('https') or query.startswith('youtube'):
                result = query
            else:
                result = f'ytsearch: {query}'

            results = await self.player.node.get_tracks(result)
            track = results['tracks'][0]

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

            self.player.add(requester=ctx.author.id, track=track)
            await self.player.play()

            embed = discord.Embed(title='Запуск музыки', color=get_embed_color(ctx.message))
            embed.add_field(name='Название:', value=f'[{title}]({uri})', inline=False)
            
            embed.add_field(name='Продолжительность:',value=lenght, inline=False)
            embed.set_footer(text=f'Добавлено: {ctx.message.author}',icon_url=ctx.message.author.avatar_url)

            await ctx.message.channel.purge(limit=1)
            await ctx.send(embed=embed)
        else:
            not_connected_embed = discord.Embed(title='Вы не подключены к голосовому каналу!', color=get_embed_color(ctx.message))
            await ctx.send(embed=not_connected_embed, delete_after=10)


    @commands.command(aliases=['стоп','с'], description='Останавливает музыку', help='Останавливает произведение музыки')
    async def stop(self, ctx):
        if self.player.is_playing:
            await self.player.stop()
            await self.connect_to(ctx.guild.id, None)
        else:
            await ctx.send('Музыка не воспроизводится!', delete_after=10)


    @commands.command(aliases=['пауза'], description="Ставит музыку на паузу", help='Приостанавливает произведение музыки')
    async def pause(self, ctx):
        if self.player.is_playing:
            self.player.set_pause(True)
        else:
            embed = discord.Embed(title='Музыка не воспроизводится!', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed, delete_after=10)


    @commands.command(description='Снимает паузу с музыки', help='')
    async def resume(self, ctx):
        if not self.player.is_playing:
            self.player.set_pause(False)
        else:
            embed = discord.Embed(title='Музыка уже играет!', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed, delete_after=10)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, lavalink.NodeException):
            ctx.send('Не удаётся подключится к серверу')



def setup(bot):
    bot.add_cog(Music(bot))