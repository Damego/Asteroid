import discord
from discord.ext import commands
import youtube_dl
import os


class Music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(aliases=['музыка','играть','муз','м'], help='Запускает музыку')
    async def play(self,ctx, url:str):

        if not ctx.message.author.voice:
            not_connected_embed = discord.Embed(title='Вы не подключены к голосовому каналу!', color=0xff0000)
            await ctx.send(embed=not_connected_embed)
            return
        else:
            voice_channel = ctx.message.author.voice.channel

        # Настройка параметров
        YDL_OPTIONS = {
            'format': 'worstaudio/best',
            'noplaylist': 'True',
            'simulate': 'True',
            'preferredquality': '192',
            'preferredcodec': 'mp3',
            'key': 'FFmpegExtractAudio'}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


        # Подключение к каналу
        
        vc = await voice_channel.connect()

        # Запуск музыки
        if vc.is_playing():
            await ctx.send(f'{ctx.message.author.mention}, музыка уже проигрывается.')

        else:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)

            URL = info['formats'][0]['url']
            title = info['title']
            duration = info['duration']
            dh = int(duration) // 3600
            dm = (int(duration) // 60) - 60
            ds = int(duration)-(dh*3600+dm*60)

            
            embed = discord.Embed(title='Запуск музыки', color=0x00ff00)
            embed.add_field(name='Название:', value=title, inline=False)
            if duration == 0.0:
                embed.add_field(name='Продолжительность:',value=f'Прямая трансляция')
            else: 
                embed.add_field(name='Продолжительность:',value=f'{dh}:{dm}:{ds}')
            embed.set_footer(text=f'Вызвано: {ctx.message.author}',icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)
            vc.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source = URL, **FFMPEG_OPTIONS))


        

    @commands.command(aliases=['стоп','с'], help='Останавливает музыку')
    async def stop(self,ctx):
        voice_client = ctx.message.guild.voice_client

        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send('Бот не подключён к каналу!')

def setup(bot):
    bot.add_cog(Music(bot))