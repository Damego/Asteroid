from asyncio import sleep
from random import choice
from time import time

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle
from discord_components.interaction import Interaction
from pymongo.collection import ReturnDocument

from .bot_settings import (
    DurationConverter,
    multiplier,
    is_administrator_or_bot_owner
    )
from .levels._levels import update_member
from mongobot import MongoComponentsBot



class Giveaways(commands.Cog, description='Розыгрыши'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🎉'


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
    @is_administrator_or_bot_owner()
    async def role(self, ctx:commands.Context, duration:DurationConverter, role:discord.Role, *, message):
        msg = await self.create_message(ctx, 'Розыгрыш Роли', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'role', role=role)


    @giveaway.command(
        name='xp',
        description='Выдаёт опыт рандомному участнику после установленного времени',
        help='[время] [опыт] [сообщение]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def xp(self, ctx:commands.Context, duration:DurationConverter, exp:int, *, message):
        msg = await self.create_message(ctx, 'Розыгрыш опыта', duration, message)
        await self.process_giveaway(ctx, duration, msg, 'exp', exp=exp)


    @commands.command(
        name='chips',
        description='Выдаёт фишки рандомному участнику после установленного времени',
        help='[время] [кол-во фишек] [сообщение]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
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

        content = f'**Участников: 0**'

        embed = discord.Embed(title=mode, color=self.bot.get_embed_color(ctx.guild.id))
        embed.description = f"""
        **Заканчивается** <t:{int(time() + timestamp)}:R>
        **Описание:** {message}
        """
        await ctx.message.delete()
        components = [
            self.bot.add_callback(
                Button(style=ButtonStyle.green, label='Принять участие'),
                self.user_register
            )
            
        ]

        message:discord.Message = await ctx.send(content=content, embed=embed, components=components)
        collection = self.bot.get_guild_giveaways_collection(ctx.guild.id)
        collection.update_one(
            {'_id':str(message.id)},
            {'$set':{
                'users':[]
            }},
            upsert=True
            )
        return message


    async def process_giveaway(self, ctx, duration, message:discord.Message, mode, *, role:discord.Role=None, exp:int=None, chips:int=None, thing:str=None):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])

        guild_id = str(ctx.guild.id)
        message_id = str(message.id)
        giveaways_collection = self.bot.get_guild_giveaways_collection(guild_id)
        users = giveaways_collection.find_one({'_id':message_id})['users']

        winner = choice(users)
        member = ctx.guild.get_member(winner)
        if member is None:
            member = await ctx.guild.fetch_member(winner)

        embed = discord.Embed(title='Итоги розыгрыша', color=self.bot.get_embed_color(guild_id))

        if mode == 'role':
            await member.add_roles(role)
            embed.description = f'Победитель, {member.mention}! Вы получаете роль: `{role}`'
        elif mode == 'exp':
            await update_member(member, exp)
            embed.description = f'Победитель, {member.mention}! Вы получаете `{exp}` опыта'
        elif mode == 'chips':
            while True:
                try:
                    users_collection = self.bot.get_guild_users_collection(guild_id)
                    user_casino = users_collection.find_one({'_id':str(member.id)})['casino']
                    users_collection.update_one(
                        {'_id':str(member.id)},
                        {'$inc':{'casino.chips':chips}}
                    )
                    embed.description = f'Победитель, {member.mention}! Вы получаете `{chips}` фишек'
                except KeyError:
                    winner = choice(users)
                    member = ctx.guild.get_member(winner)
                    if member is None:
                        member = await ctx.guild.fetch_member(winner)
                else:
                    break
        elif mode == 'thing':
            embed.description =f'Победитель, {member.mention}! Вы получаете {thing}'
        else:
            embed.description =f'Победитель, {member.mention}!'

        await ctx.send(embed=embed)
        giveaways_collection.delete_one({'_id':message_id})
        await message.delete()

    
    async def user_register(self, interaction:Interaction):
        guild_id = str(interaction.guild.id)
        message_id = str(interaction.message.id)
        user_id = str(interaction.user.id)

        collection = self.bot.get_guild_giveaways_collection(guild_id)

        users_dict = collection.find_one({'_id':message_id})
        users_list = users_dict['users']

        if user_id in users_list:
            return await interaction.send(content='Вы уже приняли участие!')

        users = collection.find_one_and_update(
            {'_id':message_id},
            {'$push':{
                'users':user_id
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        users = users['users']
        print('after', users)
        await interaction.send(content='Вы приняли участие!')
        await interaction.message.edit(content=f'**Участников: {len(users)}**')
        return



def setup(bot):
    bot.add_cog(Giveaways(bot))