import discord
from discord.ext import commands
import asyncio
import json

def get_embed_color(message):
    """Get color for embeds from json """
    with open('jsons/servers.json', 'r') as f:
        server = json.load(f)

    return int(server[str(message.guild.id)]['embed_color'], 16)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['мут'], help='Даёт мут участнику на время')
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx, member:discord.Member, time:int,* ,reason=None):
            await member.edit(mute=True)
            embed = discord.Embed(title=f'{member} был отправлен в мут!', color=get_embed_color(ctx.message))
            embed.add_field(name='Причина:', value=f'{reason}',inline=False)
            embed.add_field(name='Время:',value=f'{time / 60} минут')
            await ctx.send(embed=embed)
            await asyncio.sleep(time)
            await self.unmute(ctx, member)

    @commands.command(aliases=['дизмут', 'анмут'], help='Снимает мут с участника')
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx, member:discord.Member):
            await member.edit(mute=False)
            embed = discord.Embed(title=f'Мут с {member} снят!', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed)

    @commands.has_guild_permissions(ban_members=True)
    @commands.command(aliases=['бан'], help='Банит участника сервера')
    async def ban(self, ctx, member:discord.Member, *, reason=None):
            await member.ban(reason=reason)
            embed = discord.Embed(title=f'{member} был заблокирован!',description=f'Причина: {reason}', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed)


    @commands.command(aliases=['анбан', 'дизбан'], help='Снимает бан у участника')
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, member):
            banned_users = await ctx.guild.bans()
            member_name, member_disc = member.split('#')

            for ban in banned_users:
                user = ban.user
                if (user.name, user.discriminator) == (member_name, member_disc):
                    await ctx.guild.unban(user)
                    embed = discord.Embed(title=f'С пользователя {member} снята блокировка!', color=get_embed_color(ctx.message))
                    return await ctx.send(embed=embed)
                    

    @commands.command(aliases=['кик'], help='Кикает участника с сервера')
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason=None):
            await member.kick(reason=reason)
            embed = discord.Embed(title=f'{member} был кикнут с сервера!',description=f'Причина: {reason}', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed)


    @mute.error
    @unmute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title=f'Пользователь не подключен к голосовому каналу! {error}', color=get_embed_color(ctx.message))
            await ctx.send(embed=embed)

    @commands.command(aliases=['роль+'])
    @commands.has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, role: discord.Role): # Выдаёт роль участнику
        await member.add_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была добавлена!',color = get_embed_color(ctx.message))
        await ctx.send(embed=embed)


    @commands.command(aliases=['роль-'])
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role): # Убирает роль с участника
        await member.remove_roles(role)
        embed = discord.Embed(title=f'{member}', description=f'Роль {role} была снята!',color = get_embed_color(ctx.message)) 
        await ctx.send(embed=embed)

    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.command(aliases=['ник'])
    async def nick(self, ctx, member:discord.Member, newnick):
        oldnick = member
        await member.edit(nick=newnick)
        await ctx.send(f'{oldnick.mention} стал {newnick}')


    @commands.command(aliases=['очистить', 'очистка', 'чистить',"чист"])
    async def clear(self, ctx, amount:int):
        await ctx.channel.purge(limit=amount+1)


  

def setup(bot):
    bot.add_cog(Moderation(bot))