import asyncio
from os import getenv

import discord
from discord.ext import commands
from discord_components import Select, SelectOption, Interaction

def get_db():
    from replit import Database, db
    if db is not None:
        return db
    from dotenv import load_dotenv
    load_dotenv()
    url = getenv('URL')
    return Database(url)

def get_embed_color(guild_id):
    """Get color for embeds from json"""
    return int(server[str(guild_id)]['configuration']['embed_color'], 16)

def get_prefix(guild_id):
    """Get guild prexif from json """
    return server[str(guild_id)]['configuration']['prefix']


version = 'v1.2-beta'

server = get_db()

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



class Settings(commands.Cog, description='Настройка бота'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

        self.server = get_db()

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        guild:discord.Guild = member.guild
        guild_config = self.server[str(guild.id)]['configuration']

        if 'welcomer' not in guild_config:
            return

        guild_welcome = guild_config['welcomer']

        if 'disabled' in guild_welcome['status']:
            return

        channel_id = guild_welcome['channel']
        welcome_text = guild_welcome['text'].format(member.mention)

        channel = guild.get_channel(channel_id)

        embed = discord.Embed(description=welcome_text, color=get_embed_color(guild.id))
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
        server[str(ctx.guild.id)]['configuration']['prefix'] = prefix

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
        server[str(ctx.guild.id)]['configuration']['embed_color'] = newcolor

        embed = discord.Embed(title=f'Цвет сообщений был изменён!', color=int(newcolor, 16))
        await ctx.send(embed=embed)

    @set_conf.command(name='welcome', description='Устанавливает приветственное сообщение', help='')
    @is_administrator_or_bot_owner()
    async def welcome(self, ctx:commands.Context):
        embed = discord.Embed(color=get_embed_color(ctx.guild.id))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        if 'welcomer' not in self.server[str(ctx.guild.id)]['configuration']:
            status = 'Выкл.'
            embed.description = 'Описание'
            embed.set_footer(text='ID канала: None')
        else:
            welcomer = self.server[str(ctx.guild.id)]['configuration']['welcomer']
            status = 'Вкл.' if welcomer['status'] == 'enabled' else 'Выкл.'

            embed.description = welcomer['text']
            embed.set_footer(text=f'ID канала: {welcomer["channel"]}')

        self._welcomer_components = [
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

        message:discord.Message = await ctx.send(embed=embed, components=self._welcomer_components)

        await self._welcome_configuration(ctx, message, embed, welcomer)

    async def _welcome_configuration(self, ctx:commands.Context, message:discord.Message, embed:discord.Embed, welcomer):
        while True:
            try:
                interaction:Interaction = await self.bot.wait_for(
                    'select_option',
                    check=lambda i: i.user.id == ctx.author.id,
                    timeout=180)
            except RuntimeError:
                continue
            except asyncio.TimeoutError:
                await message.delete()
                return

            id = interaction.component[0].value
            await interaction.respond(type=6)

            channel = None

            if id == 'toggle_status':
                await self._toggle_status(message, welcomer)
            elif id == 'channel':
                channel = await self._set_welcome_channel(ctx, message, embed)
            elif id == 'desc':
                await self._edit_welcome_description(ctx, message, embed)
            elif id == 'save':
                await self._save_welcomer(interaction, embed, channel)
            elif id == 'exit':
                await message.delete()
                return

    async def _toggle_status(self, message:discord.Message):
        welcomer = self.server[str(message.guild.id)]['configuration']['welcomer']
        if 'status' in welcomer:
            if welcomer['status'] == 'enabled':
                welcomer['status'] = 'disabled'
                status = 'Выкл.'
            else:
                welcomer['status'] = 'enabled'
                status = 'Вкл.'
            self._welcomer_components[0][0].options[0].label = f'Статус: {status}'
            await message.edit(components=self._welcomer_components)
        else:
            await message.channel.send(content='Для включения/выключения сохраните!')


    @commands.command(name='prefix', description='Показывает текущий префикс на сервере', help=' ')
    async def show_guild_prefix(self, ctx:commands.Context):
        embed = discord.Embed(title=f'Текущий префикс: `{get_prefix(ctx.guild.id)}`', color=0x2f3136)
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

        
    async def _save_welcomer(self, interaction:Interaction, embed:discord.Embed=None, channel:int=None):
        bot_config = self.server[str(interaction.guild.id)]['configuration']
        if 'welcomer' not in bot_config:
            if not channel:
                return await interaction.channel.send(content='Вы не ввели ID канала!', delete_after=5)

            bot_config['welcomer'] = {
                'status': 'enabled',
                'text': embed.description,
                'channel': channel
                }

        else:
            if embed:
                bot_config['welcomer']['text'] = embed.description
            if channel:
                bot_config['welcomer']['channel'] = channel

        await interaction.channel.send(content='Сохранено!', delete_after=10)



def setup(bot):
    bot.add_cog(Settings(bot))