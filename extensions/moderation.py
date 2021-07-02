from asyncio.tasks import sleep
import discord
from discord.ext import commands

from extensions.bot_settings import DurationConverter, get_embed_color, multiplier


class Moderation(commands.Cog, description='Модерация'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['moderation', 'moder', 'mod']
        #self.spam_ls = {}

    # ! Temporaly disabled
    #@commands.Cog.listener()
    #async def on_message(self, message):
    #    if not message.author.bot:
    #        msg = message.content
    #        if msg.startswith(get_prefix(message.guild)):
    #            return
    #        if message.author.id not in self.spam_ls or msg != self.spam_ls[message.guild.id][message.channel.id][message.author.id]['message_content']:
    #            print(f'[SPAM_FILTER] {message.author} wrote message: "{message.content}"')
    #            self.spam_ls[message.guild.id] = {}
    #            self.spam_ls[message.guild.id][message.channel.id] = {}
    #            self.spam_ls[message.guild.id][message.channel.id][message.author.id] = {}
    #            self.spam_ls[message.guild.id][message.channel.id][message.author.id]['message_content'] = msg
    #            self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] = 1
#
    #        elif msg == self.spam_ls[message.guild.id][message.channel.id][message.author.id]['message_content']:
    #            print(f'[SPAM_FILTER] {message.author} wrote same message')
    #            self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] += 1
#
    #        if self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] > 2:
    #            count = self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count']
    #            self.spam_ls[message.guild.id][message.channel.id][message.author.id]['count'] = 0
#
    #            print(f'[SPAM_FILTER] Removing messages of {message.author}')
    #            await message.channel.purge(limit=count)
    #            await message.channel.send(content=f'**{message.author.mention}, Ваши сообщения были удалены из-за спама!**', delete_after=10)


    @commands.command(description='Даёт мут участнику на время', help='[Участник] [время] [причина]')
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx, member:discord.Member, duration:DurationConverter, *, reason=None):
        amount, time_format = duration
        
        muted_role = await self.get_muted_role(ctx)
        await member.add_roles(muted_role, reason=reason)
        embed = discord.Embed(title=f'{member} был отправлен в мут!', color=get_embed_color(ctx.guild.id))
        _description = f"""**Время**: {amount} {time_format}\n"""

        if reason is not None:
            _description += f'**Причина**: {reason}'
        embed.description = _description
        await ctx.send(embed=embed)

        await sleep(amount * multiplier[time_format])
        await member.remove_roles(muted_role)
        
    async def get_muted_role(self, ctx):
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
        if not muted_role:
            muted_role = await ctx.guild.create_role(name='Muted')

            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
                await sleep(0.05)
        return muted_role


    @commands.command(description='Снимает мут с участника', help='[Участник]')
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx, member:discord.Member):
        muted_role = await self.get_muted_role(ctx)
        await member.remove_roles(muted_role)
        await ctx.message.add_reaction('✅')


    @commands.has_guild_permissions(ban_members=True)
    @commands.command(description='Банит участника сервера', help='[Участник] [причина]')
    async def ban(self, ctx, member:discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.message.add_reaction('✅')
        embed = discord.Embed(title=f'{member} был заблокирован!',description=f'Причина: {reason}', color=get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @commands.command(description='Снимает бан у участника', help='[Участник]')
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, member:discord.Member):
        await member.unban()
        await ctx.message.add_reaction('✅')

                    
    @commands.command(description='Кикает участника с сервера', help='[Участник] [причина]')
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason=None):
        await member.kick(reason=reason)
        embed = discord.Embed(title=f'{member} был кикнут с сервера!',description=f'Причина: {reason}', color=get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @commands.command(aliases=['роль-'], description='Удаляет роль с участника', help='[Участник] [роль]')
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await ctx.message.add_reaction('✅')


    @commands.command(aliases=['роль+'], description='Добавляет роль участнику', help='[Участник] [роль]')
    @commands.has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await ctx.message.add_reaction('✅')


    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.command(aliases=['ник'], description='Меняет ник участнику', help='[Участник] [новый ник]')
    async def nick(self, ctx, member:discord.Member, newnick):
        await member.edit(nick=newnick)
        await ctx.message.add_reaction('✅')


    @commands.command(description='Очищает сообщения', help='[Кол-во сообщений]')
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx, amount:int):
        await ctx.channel.purge(limit=amount+1)



def setup(bot):
    bot.add_cog(Moderation(bot))