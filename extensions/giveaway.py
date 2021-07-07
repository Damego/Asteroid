from asyncio import sleep
from random import choice

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, DiscordComponents
from discord_components.interaction import Interaction

from extensions.bot_settings import get_embed_color, DurationConverter, multiplier
from ._levels import update_member



class Giveaway(commands.Cog, description='Раздача ролей'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['giveaways', 'ga']

        self.members = {}


    @commands.group(name='giveaway', aliases=['ga'], description='Выдаёт роль рандомному участнику сервера после установленного времени', help='[команда]', invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def giveaway(self, ctx:commands.Context):
        await ctx.send('Тут пока пусто. :(')


    @giveaway.command(name='role', description='Выдаёт роль рандомному участнику после установленного времени', help='[время] [роль] [сообщение]')
    @commands.has_guild_permissions(administrator=True)
    async def role(self, ctx:commands.Context, duration:DurationConverter, role:discord.Role, *, message):
        embed = discord.Embed(title='Розыгрыш роли', description=message, color=get_embed_color(ctx.guild.id))
        await self.create_message(ctx, embed)
        await self.process_giveaway(ctx, duration, 'role', role=role)


    @giveaway.command(name='xp', description='Выдаёт опыт рандомному участнику после установленного времени', help='[время] [опыт] [сообщение]')
    @commands.has_guild_permissions(administrator=True)
    async def xp(self, ctx:commands.Context, duration:DurationConverter, exp:int, *, message):
        print(type(self))
        embed = discord.Embed(title='Розыгрыш опыта', description=message, color=get_embed_color(ctx.guild.id))
        await self.create_message(ctx, embed)
        await self.process_giveaway(ctx, duration, 'exp', exp=exp)


    @giveaway.command(name='thing', description='Выдаёт символическую вещь рандомному участнику после установленного времени', help='[время] ["вещь"] [сообщение]')
    async def thing(self, ctx:commands.Context, duration:DurationConverter, thing:str, *, message):
        embed = discord.Embed(title='Розыгрыш!', description=message, color=get_embed_color(ctx.guild.id))
        await self.create_message(ctx, embed)
        await self.process_giveaway(ctx, duration, 'thing', thing=thing)

    @giveaway.command(name='random', description='Рандомно выбирает 1 участника после установленного времени', help='[время] [сообщение]')
    async def random(self, ctx:commands.Context, duration:DurationConverter, *, message):
        embed = discord.Embed(title='Розыгрыш!', description=message, color=get_embed_color(ctx.guild.id))
        await self.create_message(ctx, embed)
        await self.process_giveaway(ctx, duration, 'other')

    async def create_message(self, ctx:commands.Context, embed:discord.Embed):
        await ctx.message.delete()
        components = [
            Button(style=ButtonStyle.green, label='Принять участие', id='giveaway_accept')
        ]

        self.msg = await ctx.send(embed=embed, components=components)


    async def process_giveaway(self, ctx, duration, mode, *, role:discord.Role=None, exp:int=None, thing:str=None):
        amount, time_format = duration
        guild_id = str(ctx.guild.id)
        message_id = str(self.msg.id)

        await sleep(amount * multiplier[time_format])
        winner = choice(self.members[guild_id][message_id])
        member = await ctx.guild.fetch_member(winner)

        embed = discord.Embed(title='ИТОГИ РОЗЫГРЫША', color=get_embed_color(ctx.guild.id))

        if mode == 'role':
            await member.add_roles(role)
            embed.description = f'Победитель, {member.mention}! Вы получаете роль: `{role}`'
        elif mode == 'exp':
            await update_member(member, exp)
            embed.description =f'Победитель, {member.mention}! Вы получаете `{exp}` опыта'
        elif mode == 'thing':
            embed.description =f'Победитель, {member.mention}! Вы получаете {thing}'
        else:
            embed.description =f'Победитель, {member.mention}!'

        await ctx.send(embed=embed)
        await self.msg.delete()
        del self.members[guild_id][message_id]
    

    @commands.Cog.listener()
    async def on_button_click(self, interaction:Interaction):
        if interaction.component.id != 'giveaway_accept':
            return
        guild = str(interaction.guild.id)
        message = str(interaction.message.id)
        user = interaction.user.id

        if guild not in self.members:
            self.members[guild] = {}
        if message not in self.members[guild]:
            self.members[guild][message] = []

        try:
            if not interaction.responded:
                if user in self.members[guild][message]:
                    await interaction.respond(type=4, content='Вы уже приняли участие в этой раздаче!')
                else:
                    await interaction.respond(type=4, content='Вы приняли участие!')
                    self.members[guild][message].append(user)
        except Exception:
            pass



def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Giveaway(bot))