from asyncio import sleep
from random import choice

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, DiscordComponents

from extensions.bot_settings import get_embed_color, DurationConverter, multiplier



class Giveaway(commands.Cog, description='Раздача ролей'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['giveaways', 'ga']

        self.members = {}


    @commands.group(name='giveaway', aliases=['ga'], description='Выдаёт роль рандомному участнику сервера после установленного времени', help='[команда]', invoke_without_command=True)
    async def giveaway(self, ctx):
        await ctx.send('Тут пока пусто. :(')


    @giveaway.command(name='create', description='Создаёт раздачу', help='[время] [роль] [сообщение]')
    @commands.has_guild_permissions(administrator=True)
    async def create(self, ctx, duration:DurationConverter, role:discord.Role, *, message):
        await ctx.message.delete()

        components = [
            Button(style=ButtonStyle.green, label='Принять участие', id='giveaway_accept')
        ]

        embed = discord.Embed(title=f'Раздача роли {role}', description=message, color=get_embed_color(ctx.guild))
        self.msg = await ctx.send(embed=embed, components=components)

        isend = await self.process_giveaway(ctx, duration, role)
        if isend:
            return


    async def process_giveaway(self, ctx, duration, role):
        amount, time_format = duration

        await sleep(amount * multiplier[time_format])

        try:
            winner = choice(self.members[ctx.guild.id][self.msg.id])
            member = await ctx.guild.fetch_member(winner)
            await member.add_roles(role)

            await ctx.send(f'Победитель, {member.mention}! Вы получаете роль: `{role}`')
            del self.members[ctx.guild.id][self.msg.id]
            return True
        except KeyError:
            await ctx.send('Никто не принял участие :(')

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        if interaction.component.id != 'giveaway_accept':
            return
        guild = interaction.guild.id
        message = interaction.message.id
        user = interaction.user.id

        if not guild in self.members:
            self.members[guild] = {}
        if not message in self.members[guild]:
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