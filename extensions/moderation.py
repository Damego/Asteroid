import discord
from discord.ext import commands
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['мут'], help='Даёт мут участнику на время')
    async def mute(self, ctx, member:discord.Member, mutetime:int,* ,reason=None):
        if ctx.author.guild_permissions.administrator:
            await member.edit(mute=True)
            embed = discord.Embed(title=f'{member} был отправлен в мут!', color=0xff0000)
            embed.add_field(name='Причина:', value=f'{reason}',inline=False)
            embed.add_field(name='Время:',value=f'{int(mutetime / 60)} минут')
            await ctx.send(embed=embed)
            await asyncio.sleep(mutetime)
            await self.unmute(ctx, member)
        else:
            await self.not_enough_perms(ctx)

    @commands.command(aliases=['дизмут', 'анмут'], help='Снимает мут с участника')
    async def unmute(self, ctx, member:discord.Member):
        if ctx.author.guild_permissions.administrator:
            await member.edit(mute=False)
            embed = discord.Embed(title=f'Мут с {member} снят!', color=0xff0000)
            await ctx.send(embed=embed)
        else:
            await self.not_enough_perms(ctx)

    @commands.command(aliases=['бан'], help='Банит участника сервера')
    async def ban(self, ctx, member:discord.Member, *, reason=None):
        if ctx.author.guild_permissions.administrator:
            await member.ban(reason=reason)
            embed = discord.Embed(title=f'{member} был заблокирован!',description=f'Причина: {reason}', color=0xff0000)
            await ctx.send(embed=embed)
        else:
            await self.not_enough_perms(ctx)


    @commands.command(aliases=['анбан', 'дизбан'], help='Снимает бан у участника')
    async def unban(self, ctx, member):
        if ctx.author.guild_permissions.administrator:
            banned_users = await ctx.guild.bans()
            member_name, member_disc = member.split('#')

            for ban in banned_users:
                user = ban.user
                if (user.name, user.discriminator) == (member_name, member_disc):
                    await ctx.guild.unban(user)
                    embed = discord.Embed(title=f'С пользователя {member} снята блокировка!', color=0xff0000)
                    await ctx.send(embed=embed)
                    return
        else:
            await self.not_enough_perms(ctx)

    @commands.command(aliases=['кик'], help='Кикает участника с сервера')
    async def kick(self, ctx, member:discord.Member, *, reason=None):
        if ctx.author.guild_permissions.administrator:
            await member.kick(reason=reason)
            embed = discord.Embed(title=f'{member} был кикнут с сервера!',description=f'Причина: {reason}', color=0xff0000)
            await ctx.send(embed=embed)
        else:
            await self.not_enough_perms(ctx)

    @commands.command(hidden=True)
    async def not_enough_perms(self, ctx):
        embed = discord.Embed(title=f'У вас недостаточно прав!',color = 0x00ff00)
        await ctx.send(embed=embed)

    @mute.error
    @unmute.error
    async def mute_error(self, ctx, error):
        embed = discord.Embed(title='Пользователь не подключен к голосовому каналу!', color=0xff0000)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Moderation(bot))