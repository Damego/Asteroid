import os

import discord
from discord.ext import commands
from replit import Database, db
import youtube_dl

import lavalink

if db != None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)

def get_embed_color(message):
    """Get color for embeds from json """
    return int(server[str(message.guild.id)]['embed_color'], 16)


class Music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        print(type(self.bot))
        print(type(self.bot.user))
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
        
    @commands.command(name='play', aliases=['музыка','играть','муз','м'], description='Запускает музыку')
    async def play_music(self,ctx, *, query):
        if not ctx.message.author.voice:
            not_connected_embed = discord.Embed(title='Вы не подключены к голосовому каналу!', color=get_embed_color(ctx.message))
            await ctx.send(embed=not_connected_embed)
            return
        else:
            self.vc = ctx.message.author.voice.channel
            self.author_of_query = ctx.message.author

            player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
            if not player.is_connected:
                player.store('channel', ctx.channel.id)
                await self.connect_to(ctx.guild.id, str(vc.id))

            player = self.bot.music.player_manager.get(ctx.guild.id)
            results = await player.node.get_tracks(query)
            track = results['tracks'][0]

            title = track['info']['title']
            duration = track['info']['length']
            uri = track['info']['uri']
            dh = int(duration) // 3600
            dm = (int(duration) // 60) % 60
            ds = int(duration) % 60

            player.add(requester=ctx.author.id, track=track)
            if not player.is_playing:
                await player.play()

            embed = discord.Embed(title='Запуск музыки', color=get_embed_color(ctx.message))
            embed.add_field(name='Название', value=f'[{title}]({uri})')

            if track['info']['isStream'] is True:
                embed.add_field(name='Продолжительность:',value=f'Прямая трансляция')
            else: 
                embed.add_field(name='Продолжительность:',value=f'{dh:02}:{dm:02}:{ds:02}')

            embed.set_footer(text=f'Вызвано: {ctx.message.author}',icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)


    

    @commands.command(aliases=['стоп','с'], description='Останавливает музыку')
    async def stop(self,ctx):
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.move_members or (ctx.message.author == self.author_of_query):
            if self.vc.is_connected():
                await self.vc.disconnect()
            else:
                await ctx.send('Бот не подключён к каналу!')
        else:
            await ctx.send(f'```Музыкой управляет {self.author_of_query}!```')

    @commands.command(aliases=['пауза'], description="Ставит музыку на паузу")
    async def pause(self, ctx):
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.move_members or (ctx.message.author == self.author_of_query):
            if self.vc.is_playing():
                self.vc.pause()
            else:
                embed = discord.Embed(title='Музыка не воспроизводиться!', color=get_embed_color(ctx.message))
                await ctx.send(embed=embed)
        else:
            await ctx.send(f'```Музыкой управляет {self.author_of_query}!```')
        
    @commands.command(description='Снимает паузу с музыки')
    async def resume(self, ctx):
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.move_members or (ctx.message.author == self.author_of_query):
            if self.vc.is_playing():
                embed = discord.Embed(title='Музыка уже играет!', color=get_embed_color(ctx.message))
                await ctx.send(embed=embed)
            else:
                self.vc.resume()
        else:
            await ctx.send(f'```Музыкой управляет {self.author_of_query}!```')







def setup(bot):
    bot.add_cog(Music(bot))