import asyncio

import discord
from discord.ext import commands
from discord_components import (
    Select,
    SelectOption,
    Interaction,
    Button,
    ButtonStyle
)
from pymongo.collection import Collection
from mongobot import MongoComponentsBot


version = 'v1.2'

multiplier = {
    'д': 86400,
    'ч': 3600,
    'м': 60,
    'с': 1,
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1
    }


def is_administrator_or_bot_owner():
    async def predicate(ctx:commands.Context):
        return ctx.author.guild_permissions.administrator or ctx.author.id == ctx.bot.owner_id
    return commands.check(predicate)



class DurationConverter(commands.Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        time_format = argument[-1]

        if amount.isdigit() and time_format in ['д', 'ч', 'м', 'с', 'd', 'h', 'm', 's']:
            return (int(amount), time_format)

        raise commands.BadArgument(message='Неверный формат времени!')



async def get_interaction(bot, ctx, message):
    try:
        return await bot.wait_for(
            'button_click',
            check=lambda i: i.user.id == ctx.author.id,
            timeout=120)
    except asyncio.TimeoutError:
        await message.edit(components=[])
        return
    except Exception as e:
        print('error', e)



class PaginatorStyle:
    def style1(pages:int):
        return [[
            Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
            Button(style=ButtonStyle.green, label=f'{1}/{pages}', emoji='🏠', id='home', disabled=True),
            Button(style=ButtonStyle.gray, label='→', id='next'),
        ]]

    def style2(pages:int):
        return [[
            Button(style=ButtonStyle.gray, label='<<', id='first', disabled=True),
            Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
            Button(style=ButtonStyle.blue, label=f'{1}/{pages}', disabled=True),
            Button(style=ButtonStyle.gray, label='→', id='next'),
            Button(style=ButtonStyle.gray, label='>>', id='last')
        ]]


class PaginatorCheckButtonID:
    def __init__(self, components:list, pages:int) -> None:
        self.components = components
        self.pages = pages


    def _style1(self, button_id:int, page:int):
        if button_id == 'back':
            if page == self.pages:
                self.components[0][-1].disabled = False
            page -= 1
            if page == 1:
                self.components[0][0].disabled = True
                self.components[0][1].disabled = True
            elif page == 2:
                self.components[0][0].disabled = False
        elif button_id == 'next':
            if page == 1:
                self.components[0][0].disabled = False
                self.components[0][1].disabled = False
            page += 1
            if page == self.pages:
                self.components[0][-1].disabled = True
            elif page == self.pages-1:
                self.components[0][-1].disabled = False
        elif button_id == 'home':
            page = 1
            self.components[0][0].disabled = True
            self.components[0][1].disabled = True

        self.components[0][1].label = f'{page}/{self.pages}'
        return page

    def _style2(self, button_id:int, page:int):
        first_button = self.components[0][0]
        second_button = self.components[0][1]
        second_last_button = self.components[0][-2]
        last_button = self.components[0][-1]
        pages_button = self.components[0][2]
        if button_id == 'back':
            if page == self.pages:
                second_last_button.disabled = False
                last_button.disabled = False
            page -= 1
            if page == 1:
                first_button.disabled = True
                second_button.disabled = True
            elif page == 2:
                first_button.disabled = False
                second_button.disabled = False

        elif button_id == 'first':
            page = 1
            first_button.disabled = True
            second_button.disabled = True
            second_last_button.disabled = False
            last_button.disabled = False

        elif button_id == 'last':
            page = self.pages
            first_button.disabled = False
            second_button.disabled = False
            second_last_button.disabled = True
            last_button.disabled = True

        elif button_id == 'next':
            if page == 1:
                first_button.disabled = False
                second_button.disabled = False
            page += 1
            if page == self.pages:
                second_last_button.disabled = True
                last_button.disabled = True
            elif page == self.pages-1:
                second_last_button.disabled = False
                last_button.disabled = False
        pages_button.label = f'{page}/{self.pages}'

        return page



class Settings(commands.Cog, description='Настройка бота'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🔧'

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        guild:discord.Guild = member.guild
        guild_configuration_collection = self.bot.get_guild_configuration_collection(member.guild.id)
        guild_configuration = guild_configuration_collection.find()
        if 'welcomer' not in guild_configuration:
            return

        guild_welcome = guild_configuration['welcomer']

        if 'disabled' in guild_welcome['status']:
            return

        channel_id = guild_welcome['channel']
        welcome_text = guild_welcome['text'].format(member.mention)

        channel = guild.get_channel(channel_id)

        embed = discord.Embed(description=welcome_text, color=self.bot.get_embed_color(guild.id))
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await channel.send(embed=embed)

    @is_administrator_or_bot_owner()
    @commands.group(
        invoke_without_command=True,
        name='set',
        description='Команда, позволяющая изменять настройки бота',
        help='[команда]',
        usage='Только для Администрации')
    async def set_conf(self, ctx:commands.Context):
        await ctx.send('Используйте команды: `set prefix` или `set color`', delete_after=10)

    
    @set_conf.command(
        name='prefix',
        aliases=['префикс'],
        description='Меняет префикс для команд',
        help='[префикс]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def change_guild_prefix(self, ctx:commands.Context, prefix):
        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one({'_id':'configuration'}, {'$set':{'prefix':prefix}})

        embed = discord.Embed(title=f'Префикс для команд изменился на `{prefix}`', color=0x2f3136)
        await ctx.send(embed=embed, delete_after=30)

    @set_conf.command(
        name='color',
        aliases=['цвет'],
        description='Меняет цвет сообщений бота',
        help='[цвет(HEX)]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def change_guild_embed_color(self, ctx:commands.Context, color:str):
        if color.startswith('#') and len(color) == 7:
            color = color.replace('#', '')
        elif len(color) != 6:
            await ctx.send('Неверный формат цвета')
            return
            
        newcolor = '0x' + color

        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one({'_id':'configuration'}, {'$set':{'embed_color':newcolor}}, upsert=True)

        embed = discord.Embed(title=f'Цвет сообщений был изменён!', color=int(newcolor, 16))
        await ctx.send(embed=embed)

    @set_conf.command(name='welcome', description='Устанавливает приветственное сообщение', help='')
    @is_administrator_or_bot_owner()
    async def welcome(self, ctx:commands.Context):
        embed = discord.Embed(color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        welcomer = collection.find_one({'_id':'configuration'}, 'welcomer')

        if welcomer is None:
            status = 'Выкл.'
            embed.description = 'Описание'
            embed.set_footer(text='ID канала: None')
        else:
            status = 'Вкл.' if welcomer['status'] == 'enabled' else 'Выкл.'

            embed.description = welcomer['text']
            embed.set_footer(text=f'ID канала: {welcomer["channel"]}')

        welcomer_components = [
            Select(
                placeholder='Выберите опцию',
                options=[
                    SelectOption(label=f'Статус: {status}', value='toggle_status'),
                    SelectOption(label='Установить канал', value='channel'),
                    SelectOption(label='Установить описание', value='desc'),
                    SelectOption(label='Сохранить', value='save'),
                    SelectOption(label='Выйти', value='exit')
                ]
            )
        ]

        message:discord.Message = await ctx.send(embed=embed, components=welcomer_components)

        await self._welcome_configuration(ctx, message, embed, welcomer_components, collection)

    async def _welcome_configuration(self, ctx:commands.Context, message:discord.Message, embed:discord.Embed, components, collection):
        while True:
            try:
                interaction:Interaction = await self.bot.wait_for(
                    'select_option',
                    check=lambda i: i.user.id == ctx.author.id,
                    timeout=180)
            except RuntimeError:
                continue
            except asyncio.TimeoutError:
                return await message.delete()

            id = interaction.values[0]
            await interaction.respond(type=6)

            channel = None

            if id == 'toggle_status':
                await self._toggle_status(message, components, collection)
            elif id == 'channel':
                channel = await self._set_welcome_channel(ctx, message, embed)
            elif id == 'desc':
                await self._edit_welcome_description(ctx, message, embed)
            elif id == 'save':
                await self._save_welcomer(interaction, collection, embed, channel)
            elif id == 'exit':
                return await message.delete()


    async def _toggle_status(self, message:discord.Message, components, collection:Collection):
        status = collection.find_one({'_id':'configuration'})['welcomer'].get('status')
        if status is not None:
            if status == 'enabled':
                collection.update_one({'_id':'configuration'}, {'$set':{'welcomer.status':'disabled'}}, upsert=True)
                status = 'Выкл.'
            else:
                collection.update_one({'_id':'configuration'}, {'$set':{'welcomer.status':'enabled'}}, upsert=True)
                status = 'Вкл.'
            components[0][0].options[0].label = f'Статус: {status}'
            await message.edit(components=components)
        else:
            await message.channel.send(content='Для включения/выключения сохраните!')


    @commands.command(name='prefix', description='Показывает текущий префикс на сервере', help=' ')
    async def show_guild_prefix(self, ctx:commands.Context):
        embed = discord.Embed(title=f'Текущий префикс: `{self.bot.get_guild_prefix(ctx.guild.id)}`', color=0x2f3136)
        await ctx.send(embed=embed)


    @commands.command(aliases=['cl'], name='changelog', description='Показывает изменения последнего обновления', help='')
    async def changelog(self, ctx:commands.Context):
        with open('changelog.txt', 'r', encoding='UTF-8') as file:
            version = file.readline()
            text = file.read()

        embed = discord.Embed(title=version, description=text, color=0x2f3136)
        await ctx.send(embed=embed)


    async def _set_welcome_channel(self, ctx:commands.Context, menu_message:discord.Message, embed:discord.Embed):
        message:discord.Message = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id)
        content = message.content

        await ctx.send(content=f'Введите id канала', delete_after=5)
        
        try:
            channel_id = int(content)
        except Exception:
            await ctx.send('Введите id канала!', delete_after=5)
            return
        else:
            await message.delete()

            embed.set_footer(text=f'ID канала: {channel_id}')
            await menu_message.edit(embed=embed)
            return channel_id


    async def _edit_welcome_description(self, ctx:commands.Context, menu_message:discord.Message, embed:discord.Embed):
        await ctx.send(content=f'Введите описание', delete_after=5)
    
        message:discord.Message = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id)
        content = message.content
        embed.description = content
        await message.delete()
        await menu_message.edit(embed=embed)


    async def _save_welcomer(self, interaction:Interaction, collection:Collection, embed:discord.Embed=None, channel:int=None):
        if channel is None:
            channel = collection.find_one({'_id':'configuration'}).get('welcomer').get('channel')
            if channel is None:
                return await interaction.channel.send(content='Вы не ввели ID канала!', delete_after=5)

            welcomer = {
                'status': 'enabled',
                'text': embed.description,
                'channel': channel
                }

            collection.update_one(
                {'_id':'configuration'},
                {'$set':{'configuration.welcomer':welcomer}},
                upsert=True
            )

        else:
            if embed is not None:
                collection.update_one(
                {'_id':'configuration'},
                {'$set':{'configuration.welcomer.text':embed.description}},
                upsert=True
            )
            if channel is not None:
                collection.update_one(
                {'_id':'configuration'},
                {'$set':{'configuration.welcomer.channel':channel}},
                upsert=True
            )

        await interaction.channel.send(content='Сохранено!', delete_after=10)



def setup(bot):
    bot.add_cog(Settings(bot))