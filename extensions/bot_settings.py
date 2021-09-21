import asyncio

import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions
from discord_components import (
    Select,
    SelectOption,
    Interaction,
    Button,
    ButtonStyle
)
from mongobot import MongoComponentsBot


version = 'Special version for discord_components'

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
        if not ctx.author.guild_permissions.administrator or ctx.author.id != 143773579320754177:
            raise MissingPermissions(['Administrator'])
        return True
    return commands.check(predicate)



class DurationConverter(commands.Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        time_format = argument[-1]

        if amount.isdigit() and time_format in ['д', 'ч', 'м', 'с', 'd', 'h', 'm', 's']:
            return (int(amount), time_format)

        raise commands.BadArgument(message='Wrong time format!')



async def get_interaction(bot, ctx, message):
    try:
        return await bot.wait_for(
            'button_click',
            check=lambda i: i.user.id == ctx.author.id and i.message.id == ctx.message.id,
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



class Settings(commands.Cog, description='Settings'):
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
        description='Command for change bot settings',
        help='[subcommand]',
        usage='Only for Admins')
    async def set_conf(self, ctx:commands.Context):
        ...

    
    @set_conf.command(
        name='prefix',
        description='Change prefix for the guild',
        help='[prefix]',
        usage='Only for Admins')
    @is_administrator_or_bot_owner()
    async def change_guild_prefix(self, ctx:commands.Context, prefix):
        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one({'_id':'configuration'}, {'$set':{'prefix':prefix}})

        embed = discord.Embed(title=f'Prefix for commands was changed to `{prefix}`', color=0x2f3136)
        await ctx.send(embed=embed, delete_after=30)

    @set_conf.command(
        name='color',
        description='Change color for Embeds',
        help='[color(HEX)]',
        usage='Only for Admins')
    @is_administrator_or_bot_owner()
    async def change_guild_embed_color(self, ctx:commands.Context, color:str):
        if color.startswith('#') and len(color) == 7:
            color = color.replace('#', '')
        elif len(color) != 6:
            await ctx.send('Wrong format!')
            return
            
        newcolor = '0x' + color

        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one({'_id':'configuration'}, {'$set':{'embed_color':newcolor}}, upsert=True)

        embed = discord.Embed(title=f'Embed color was changed!', color=int(newcolor, 16))
        await ctx.send(embed=embed, delete_after=10)

    
    @commands.command(name='prefix', description='Show current prefix for this server', help='')
    async def show_guild_prefix(self, ctx:commands.Context):
        embed = discord.Embed(title=f'Current prefix: `{self.bot.get_guild_prefix(ctx.guild.id)}`', color=0x2f3136)
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Settings(bot))