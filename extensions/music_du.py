import discord
from discord import player
from discord.ext import commands
import DiscordUtils

class MusicDU(commands.Cog, description='NEW Music player'):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.hidden = False
        self.music = DiscordUtils.Music()

    @commands.command(description='None', help='None')
    async def du_play(self, ctx, url):
        await ctx.author.voice.channel.connect()
        player = self.music.get_player(guild_id=ctx.guild.id)
        if not player:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)
        if not ctx.voice_client.is_playing():
            await player.queue(url, search=True)
            track = await player.play()
            await ctx.send(f'Now playing {track.name}')

    @commands.command(description='None', help='None')
    async def du_stop(self, ctx):
        player = self.music.get_player(guild_id=ctx.guild.id)
        await player.stop()
        await ctx.send("Stopped")

def setup(bot):
    bot.add_cog(MusicDU(bot))