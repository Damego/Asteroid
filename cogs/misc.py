import asyncio
import json
from os import remove, environ
from random import choice, randint

import discord
from discord.errors import Forbidden
from discord.ext.commands import Cog
from discord_components import Select, SelectOption, Button, ButtonStyle
from discord_slash import SlashContext, ContextMenuType, MenuContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu,
)
from discord_slash_components_bridge import ComponentContext
import qrcode
import requests

from my_utils import AsteroidBot, get_content
from ._hltv import HLTV
from .settings import guild_ids



class Misc(Cog, description='Misc commands'):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '💡'
        self.name = 'misc'


    @slash_subcommand(
        base='fun',
        name='random',
        description='Generate random number',
        guild_ids=guild_ids
    )
    async def random_num(self, ctx: SlashContext, _from: int, _to: int):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_RANDOM_NUMBER_OUT_CONTENT', lang)

        random_number = randint(_from, _to)
        await ctx.reply(content.format(random_number))


    @slash_subcommand(
        base='fun',
        name='coinflip',
        description='flip a coin',
        guild_ids=guild_ids
    )
    async def coinflip(self, ctx: SlashContext):
        result = randint(0,1)
        if result:
            content = '<:eagle_coin:855061929827106818>'
        else:
            content = '<:tail_coin:855060316609970216>'

        await ctx.reply(content)


    @slash_command(
        name='info',
        description='Out information about guild member',
        guild_ids=guild_ids
        )
    async def get_member_information_slash(self, ctx: SlashContext, member: discord.Member=None):
        if member is None:
            member = ctx.author
        embed = self._get_embed_member_info(ctx, member)
        await ctx.send(embed=embed)


    @context_menu(
        name='Get information',
        guild_ids=guild_ids,
        target=ContextMenuType.MESSAGE
    )
    async def get_member_information_context(self, ctx: MenuContext):
        member = ctx.target_message.author
        embed = self._get_embed_member_info(ctx, member)
        await ctx.send(embed=embed)


    def _get_embed_member_info(self, ctx, member: discord.Member) -> discord.Embed:
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_MEMBER_INFO', lang=lang)
        status = content.get('MEMBER_STATUS')
        about_text = content.get('ABOUT_TITLE').format(member)
        gen_info_title_text = content.get('GENERAL_INFO_TITLE')
        date_reg_discord_text = content.get('DISCORD_REGISTRATION_TEXT')
        date_joined_server_text = content.get('JOINED_ON_SERVER_TEXT')
        current_status_text = content.get('CURRENT_STATUS_TEXT')
        roles_text = content.get('ROLES')
        
        embed = discord.Embed(title=about_text, color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_thumbnail(url=member.avatar_url)

        member_roles = [role.mention for role in member.roles if role.name != "@everyone"][::-1]
        member_roles = ', '.join(member_roles)
        member_status = str(member.status)

        embed.add_field(name=gen_info_title_text, value=f"""
            {date_reg_discord_text} <t:{int(member.created_at.timestamp())}:F>
            {date_joined_server_text} <t:{int(member.joined_at.timestamp())}:F>
            {current_status_text} {status.get(member_status)}
            {roles_text} {member_roles}
            """, inline=False)

        return embed


    @slash_subcommand(
        base='fun',
        name='qr',
        description='Create a QR-code',
        guild_ids=guild_ids
    )
    async def create_qr(self, ctx: SlashContext, *, text):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1
        )
        qr.add_data(data=text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f'./qrcodes/{ctx.author.id}.png')
        await ctx.send(file = discord.File(f'./qrcodes/{ctx.author.id}.png'))
        remove(f'./qrcodes/{ctx.author.id}.png')


    @slash_subcommand(
        base='misc',
        name='ping',
        description='Show bot latency',
        guild_ids=guild_ids
    )
    async def ping(self, ctx: SlashContext):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_PING', lang=lang)

        embed = discord.Embed(title='🏓 Pong!', description=content.format(int(self.bot.latency * 1000)), color=self.bot.get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @slash_subcommand(
        base='fun',
        name='activity',
        description='Open discord Activities',
        guild_ids=guild_ids
    )
    async def start_activity(self, ctx: SlashContext):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_ACTIVITIES', lang=lang)
        not_connected_text = content.get('NOT_CONNECTED_TO_CHANNEL_TEXT')
        choose_activity = content.get('CHOOSE_ACTIVITY_TEXT')

        if not ctx.author.voice:
            return await ctx.send(not_connected_text)

        channel_id = ctx.author.voice.channel.id
        components = [
            [
                Button(style=ButtonStyle.red, label='YouTube', custom_id='755600276941176913'),
                Button(style=ButtonStyle.blue, label='Betrayal.io', custom_id='773336526917861400'),
                Button(style=ButtonStyle.blue, label='Fishington.io', custom_id='814288819477020702'),
                Button(style=ButtonStyle.gray, label='Poker Night', custom_id='755827207812677713'),
                Button(style=ButtonStyle.green, label='Chess', custom_id='832012774040141894'),
            ]
        ]
        message = await ctx.send(choose_activity,
            components=components
        )

        interaction = await self.bot.wait_for('button_click', check=lambda inter: inter.author.id == ctx.author_id and inter.message.id == message.id)
        await message.delete()

        data = self._get_data(int(interaction.custom_id))
        headers = {
            'Authorization': f'Bot {environ.get("BOT_TOKEN")}',
            'Content-Type': 'application/json'
        }

        responce = requests.post(f'https://discord.com/api/v8/channels/{channel_id}/invites', data=json.dumps(data), headers=headers)
        code = json.loads(responce.content).get('code')
        if code == '50013':
            raise Forbidden
        
        await interaction.send(f'https://discord.com/invite/{code}')
        
    def _get_data(self, application_id: int):
        return {
            'max_age': 86400,
            'max_uses': 0,
            'target_application_id': application_id,
            'target_type': 2,
            'temporary': False,
            'validate': None
        }

    
    @slash_subcommand(
        base='phasmo',
        name='item',
        guild_ids=guild_ids
    )
    async def phasmophobia_random_item(self, ctx: SlashContext):
        await self._start_random(ctx)


    @slash_subcommand(
        base='phasmo',
        name='map',
        guild_ids=guild_ids
    )
    async def phasmophobia_random_map(self, ctx: SlashContext):
        maps_list = [
            'Bleasdale Farmhouse',
            'Edgefield Street House',
            'Grafton Farmhouse',
            'Ridgeview Road House',
            'Tanglewood Street House',
            'Willow Street House',
            'Brownstone High School',
            'Prison',
            'Asylum'
        ]

        await self._start_random(ctx, maps_list)


    async def _start_random(self, ctx: SlashContext, _list: list=None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_PHASMOPHOBIA_RANDOM', lang)
        if _list is None:
            _list = content['ITEMS_LIST']
        components = [
            Button(style=ButtonStyle.blue, label=content['SELECT_BUTTON'], custom_id='toggle'),
            Select(
                placeholder=content['SELECT_ITEMS_TEXT'],
                options=[SelectOption(label=item, value=item) for item in _list],
                max_values=len(_list)
            ),
            [
                Button(label=content['START_RANDOM_BUTTON'], custom_id='start_random', style=ButtonStyle.green),
                Button(label=content['EXIT_BUTTON'], custom_id='exit', style=ButtonStyle.red),
            ]
        ]
        selected = None
        is_exception = False
        is_removed = False
        embed = discord.Embed(title=content['EMBED_TITLE'])

        message = await ctx.send(embed=embed, components=components)
        message_for_update = await ctx.send(content['SECOND_MESSAGE_CONTENT'])

        while True:
            try:
                interaction = await self._get_interaction(ctx, message, message_for_update)
            except asyncio.TimeoutError:
                return

            if isinstance(interaction.component, Select):
                selected = interaction.values
                if is_exception:
                    _selected = _list.copy()
                    for item in selected:
                        _selected.remove(item)
                    selected = _selected
                embed.description = content['SELECTED_ITEMS_TEXT'] + ', '.join(selected)
                await interaction.edit_origin(embed=embed)

            elif interaction.custom_id == 'toggle':
                is_exception = not is_exception
                interaction.component.label = content['EXCEPTION_BUTTON'] if is_exception else content['SELECT_BUTTON']
                selected = None
                is_removed = False
                embed.description = ''

                await interaction.edit_origin(embed=embed, components=interaction.message.components)

            elif interaction.custom_id == 'start_random':
                if not is_exception and selected is not None:
                    item = choice(selected)
                    await message_for_update.edit(content=item)

                elif is_exception and selected is not None:
                    if not is_removed:
                        is_removed = True
                        items = _list.copy()
                        for item in selected:
                            items.remove(item)
                    item = choice(selected)
                    await message_for_update.edit(content=item)
                elif is_exception:
                    selected = _list
                    item = choice(selected)
                    await message_for_update.edit(content=item)

            elif interaction.custom_id == 'exit':
                await message.delete()
                await message_for_update.delete()
                return

    async def _get_interaction(self, ctx: SlashContext, message, message_for_update):
        try:
            interaction: ComponentContext = await self.bot.wait_for(
                'component',
                check=lambda inter: inter.author_id == ctx.author_id and inter.message.id == message.id,
                timeout=3600
            )
        except asyncio.TimeoutError:
            await message.delete()
            await message_for_update.delete()
            raise asyncio.TimeoutError
        else:
            await interaction.defer(edit_origin=True)
            return interaction



def setup(bot):
    bot.add_cog(Misc(bot))
