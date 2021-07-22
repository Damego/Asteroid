from asyncio import sleep
from random import choice
from time import time

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle
from discord_components.interaction import Interaction

from .bot_settings import get_embed_color, DurationConverter, multiplier
from ._levels import update_member



class Giveaways(commands.Cog, description='Розыгрыши'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False


    @commands.group(
        name='giveaway',
        aliases=['ga'],
        description='Основная команда для розыгрышей',
        help='[команда]',
        invoke_without_command=True)
    async def giveaway(self, ctx:commands.Context):
        await ctx.send('Тут пока пусто. :(')


    @giveaway.command(
        name='role',
        description='Выдаёт роль рандомному участнику после установленного времени',
        help='[время] [роль] [сообщение]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def role(self, ctx:commands.Context, duration:DurationConverter, role:discord.Role, *, message):
        msg = await self.create_message(ctx, 'Розыгрыш Роли', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'role', role=role)


    @giveaway.command(
        name='xp',
        description='Выдаёт опыт рандомному участнику после установленного времени',
        help='[время] [опыт] [сообщение]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def xp(self, ctx:commands.Context, duration:DurationConverter, exp:int, *, message):
        msg = await self.create_message(ctx, 'Розыгрыш опыта', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'exp', exp=exp)


    @commands.command(
        name='chips',
        description='Выдаёт фишки рандомному участнику после установленного времени',
        help='[время] [кол-во фишек] [сообщение]',
        usage='Только для Администрации')
    async def chips(self, ctx:commands.Context, duration:DurationConverter, chips:int, *, message):
        msg = await self.create_message(ctx, 'Розыгрыш фишек', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'chips', chips=chips)


    @giveaway.command(
        name='thing',
        description='Выдаёт символическую вещь рандомному участнику после установленного времени',
        help='[время] ["вещь"] [сообщение]')
    async def thing(self, ctx:commands.Context, duration:DurationConverter, thing:str, *, message):
        msg = await self.create_message(ctx, 'Розыгрыш', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'thing', thing=thing)


    @giveaway.command(
        name='random',
        description='Рандомно выбирает 1 участника после установленного времени',
        help='[время] [сообщение]')
    async def random(self, ctx:commands.Context, duration:DurationConverter, *, message):
        msg = await self.create_message(ctx, 'Рандомный пользователь', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'other')


    async def create_message(self, ctx:commands.Context, mode, duration:DurationConverter, message:discord.Message):
        amount, time_format = duration
        timestamp = amount * multiplier[time_format]

        if 'giveaways_members' not in self.server[str(ctx.guild.id)]:
            self.server[str(ctx.guild.id)]['giveaways_members'] = {}
        self.members = self.server[str(ctx.guild.id)]['giveaways_members']

        self.members[str(ctx.message.id)] = []

        content = f'**Участников: {len(self.members[str(ctx.message.id)])}**'

        embed = discord.Embed(title=mode, color=get_embed_color(ctx.guild.id))
        embed.description = f"""
        **Заканчивается** <t:{int(time() + timestamp)}:R>
        **Описание:** {message}
        """
        await ctx.message.delete()
        components = [
            Button(style=ButtonStyle.green, label='Принять участие', id='giveaway_accept')
        ]

        return await ctx.send(content=content, embed=embed, components=components)


    async def process_giveaway(self, ctx, duration, message:discord.Message, mode, *, role:discord.Role=None, exp:int=None, chips:int=None, thing:str=None):
        amount, time_format = duration
        guild_id = str(ctx.guild.id)
        message_id = str(message.id)

        await sleep(amount * multiplier[time_format])
        winner = choice(self.members[message_id])
        member = await ctx.guild.fetch_member(winner)

        embed = discord.Embed(title='ИТОГИ РОЗЫГРЫША', color=get_embed_color(guild_id))

        if mode == 'role':
            await member.add_roles(role)
            embed.description = f'Победитель, {member.mention}! Вы получаете роль: `{role}`'
        elif mode == 'exp':
            await update_member(member, exp)
            embed.description =f'Победитель, {member.mention}! Вы получаете `{exp}` опыта'
        elif mode == 'chips':
            while True:
                try:
                    self.server[str(guild_id)]['users'][str(member.id)]['casino']['chips'] += chips
                    embed.description =f'Победитель, {member.mention}! Вы получаете `{chips}` фишек'
                except KeyError:
                    winner = choice(self.members[message_id])
                    member = await ctx.guild.fetch_member(winner)
                else:
                    break
        elif mode == 'thing':
            embed.description =f'Победитель, {member.mention}! Вы получаете {thing}'
        else:
            embed.description =f'Победитель, {member.mention}!'

        await ctx.send(embed=embed)
        await message.delete()
        del self.members[message_id]
    

    @commands.Cog.listener()
    async def on_button_click(self, interaction:Interaction):
        if interaction.component.id != 'giveaway_accept':
            return
        guild_id = str(interaction.guild.id)
        message_id = str(interaction.message.id)
        user_id = interaction.user.id

        try:
            if not interaction.responded:
                if user_id in self.members[message_id]:
                    await interaction.respond(type=4, content='Вы уже приняли участие в этой раздаче!')
                else:
                    await interaction.respond(type=4, content='Вы приняли участие!')
                    self.members[message_id].append(user_id)
                    message = interaction.message
                    await message.edit(content=f'**Участников: {len(self.members[message_id])}**')
        except Exception:
            pass



def setup(bot):
    bot.add_cog(Giveaways(bot))