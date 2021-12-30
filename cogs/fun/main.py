import asyncio
from datetime import datetime
import json
from os import remove, environ
from random import choice, randint

from discord import Embed, Member, Forbidden, File, VoiceChannel
from discord_slash import SlashContext, ContextMenuType, MenuContext
from discord_slash.cog_ext import (
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu
)
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash_components_bridge import ComponentContext
from discord_components import Button, ButtonStyle, Select, SelectOption
import qrcode
import requests

from my_utils import AsteroidBot, get_content, Cog, is_enabled
from ._tictactoe_online import TicTacToeOnline, BoardMode
from ._tictactoe_ai import TicTacToeAI, TicTacToeMode
from ._rockpaperscissors import RockPaperScissors
from ._calculator import Calculator


bored_api_types = ["education", "recreational", "social", "diy", "charity", "cooking", "relaxation", "music",
                   "busywork"]
discord_activities_list = {
    'YouTube': '880218394199220334',
    'Betrayal.io': '773336526917861400',
    'Fishington.io': '814288819477020702',
    'Poker Night': '755827207812677713',
    'Chess': '832012774040141894',
    'Word Snack': '879863976006127627',
    'Letter Tile': '879863686565621790',
    'Doodle Crew': '878067389634314250',
    'awkword': '879863881349087252',
    'spellcast': '852509694341283871',
    'checkers': '832013003968348200',
    'puttparty': '763133495793942528'
}


class Fun(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.name = 'Fun'
        self.emoji = '🎮'

    @slash_subcommand(
        base='game',
        name='rps',
        description='Start play a Rock Paper Scissors'
    )
    @is_enabled()
    async def rockpaperscissors_cmd(self, ctx: SlashContext, member: Member, total_rounds: int=3):
        await self._start_rps(ctx, member, total_rounds)

    @context_menu(
        target=ContextMenuType.USER,
        name='Start Rock Paper Scissors'
    )
    @is_enabled()
    async def rockpaperscissors_contex(self, ctx: MenuContext):
        member = ctx.target_author
        await self._start_rps(ctx, member, 3)

    async def _start_rps(self, ctx: SlashContext, member: Member, total_rounds: int):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_INVITE_TO_GAME', lang)
        
        if member.id == ctx.author_id:
            return await ctx.send(content['SELF_INVITE'])
            
        game_name = get_content('GAMES_NAMES', lang)['RPS']
        message, accept = await self.invite_to_game(ctx, member, game_name)

        if not accept:
            return

        game = RockPaperScissors(self.bot, ctx, member, message, total_rounds)
        await game.start_game()

    @slash_subcommand(
        base='game',
        subcommand_group='ttt',
        name='online',
        description='Play a TicTacToe game Online',
        options=[
            create_option(
                name='member',
                description='Whoever you want to play with',
                required=True,
                option_type=6
            ),
            create_option(
                name='mode',
                description='Choose mode of game (3x3, 4x4, 5x5)',
                required=False,
                option_type=3,
                choices=[
                    create_choice(
                        name='3x3',
                        value='3x3'
                    ),
                    create_choice(
                        name='4x4',
                        value='4x4'
                    ),
                    create_choice(
                        name='5x5',
                        value='5x5'
                    ),
                ]
            )
        ]
    )
    @is_enabled()
    async def tictactoe_cmd(self, ctx: SlashContext, member: Member, mode: str = '3x3'):
        await self.start_tictactoe_online(ctx, member, mode)

    @slash_subcommand(
        base='game',
        subcommand_group='ttt',
        name='bot',
        description='Play a TicTacToe game with bot!'
    )
    @is_enabled()
    async def ttt_game_ai(self, ctx: SlashContext):
        components = [
            [
                Button(label='Easy', style=ButtonStyle.blue, custom_id='ttt_easy'),
                Button(label='Impossible', style=ButtonStyle.blue, custom_id='ttt_imp')
            ]
        ]
        embed = Embed(
            title='Tic Tac Toe Game',
            description="**Choose a difficult:**"
                        "\n`Easy` - Bot random clicks on free cell"
                        "\n`Impossible` - Bot with minimax AI.",
            color=self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        message = await ctx.send(
            embed=embed,
            components=components
        )

        try:
            _ctx: ComponentContext = await self.bot.wait_for(
                'button_click',
                check=lambda __ctx: __ctx.author_id == ctx.author_id and __ctx.message.id == message.id,
                timeout=60
            )
        except asyncio.TimeoutError:
            return await message.delete()

        if _ctx.custom_id == 'ttt_easy':
            mode = TicTacToeMode.easy
        else:
            mode = TicTacToeMode.impossible

        ttt = TicTacToeAI(self.bot, _ctx, mode=mode)
        await ttt.start(edit_origin=True, message=message)

    async def start_tictactoe_online(self, ctx, member: Member, mode: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        invite_content = get_content('FUNC_INVITE_TO_GAME', lang)
        game_content = get_content('GAME_TTT', lang)
        game_name = get_content('GAMES_NAMES', lang)['TTT']

        if member.id == ctx.author_id:
            return await ctx.send(invite_content['SELF_INVITE'])
        if member.bot:
            return await ctx.send(invite_content['BOT_INVITE'])
            
        message, accept = await self.invite_to_game(ctx, member, game_name)
        if not accept:
            return

        if mode == '3x3':
            board_mode = BoardMode.x3
        elif mode == '4x4':
            board_mode = BoardMode.x4
        elif mode == '5x5':
            board_mode = BoardMode.x5

        game = TicTacToeOnline(self.bot, message, ctx, member, game_content, board_mode)
        await game.start_game()

    async def invite_to_game(self, ctx, member, game_name):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_INVITE_TO_GAME', lang)
        button_label_agree = content['BUTTON_AGREE']
        button_label_decline = content['BUTTON_DECLINE']
        invite_text = content['INVITE_MESSAGE_CONTENT'].format(
            member.mention, ctx.author.name, game_name
        )

        def member_agree(interaction):
            return interaction.author_id == member.id

        components = [
            [
                Button(style=ButtonStyle.green, label=button_label_agree, custom_id='agree'),
                Button(style=ButtonStyle.red, label=button_label_decline, custom_id='decline')
            ]
        ]

        message = await ctx.send(
            content=invite_text,
            components=components
        )

        if member.bot:
            embed = Embed(
                title=game_name,
                description=f'{ctx.author.display_name} VS {member.display_name}',
                color=self.bot.get_embed_color(ctx.guild.id)
            )
            await message.edit(content=' ', embed=embed)
            return message, True
            
        try:
            interaction: ComponentContext = await self.bot.wait_for('button_click', check=member_agree, timeout=60)
            accepted_invite = content['AGREE_MESSAGE_CONTENT']
            await interaction.send(accepted_invite, hidden=True)
        except TimeoutError:
            timeout_error = content['TIMEOUT_MESSAGE_CONTENT'].format(member.display_name)
            await message.edit(content=timeout_error, components=[])
            return message, False

        if interaction.custom_id == 'agree':
            embed = Embed(
                title=game_name,
                description=f'{ctx.author.display_name} VS {member.display_name}',
                color=self.bot.get_embed_color(ctx.guild.id)
            )
            await message.edit(content=' ', embed=embed)
            return message, True

        declined_invite = content['DECLINE_MESSAGE_CONTENT'].format(member.display_name)
        await message.edit(content=declined_invite, components=[])
        return message, False

    @slash_subcommand(
        base='fun',
        name='random_num',
        description='Generate random number'
    )
    @is_enabled()
    async def random_num(self, ctx: SlashContext, _from: int, _to: int):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_RANDOM_NUMBER_OUT_CONTENT', lang)

        random_number = randint(_from, _to)
        await ctx.reply(content.format(random_number))

    @slash_subcommand(
        base='fun',
        name='qr',
        description='Create a QR-code'
    )
    @is_enabled()
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
        await ctx.send(file=File(f'./qrcodes/{ctx.author.id}.png'))
        remove(f'./qrcodes/{ctx.author.id}.png')

    @slash_subcommand(
        base='fun',
        name='activity',
        description='Open discord Activities',
        options=[
            create_option(
                name='activity',
                description='Choose discord activity',
                option_type=3,
                required=True,
                choices=[create_choice(
                    name=activity,
                    value=activity)
                    for activity in discord_activities_list
                ]
            ),
            create_option(
                name='channel',
                description='Choose voice channel',
                required=False,
                option_type=7
            )
        ]
    )
    @is_enabled()
    async def start_activity(self, ctx: SlashContext, activity: str, channel: VoiceChannel = None):
        await ctx.defer()
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_ACTIVITIES', lang=lang)

        if not channel and not ctx.author.voice:
            return await ctx.send(content['NOT_CONNECTED_TO_CHANNEL_TEXT'])
        if channel and not isinstance(channel, VoiceChannel):
            return await ctx.send(content['WRONG_CHANNEL_TEXT'])
        if not channel:
            channel = ctx.author.voice.channel

        data = self._get_data(int(discord_activities_list[activity]))
        headers = {
            'Authorization': f'Bot {environ.get("BOT_TOKEN")}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'https://discord.com/api/v8/channels/{channel.id}/invites',
            data=json.dumps(data),
            headers=headers
        )
        code = json.loads(response.content).get('code')
        if code == '50013':
            raise Forbidden

        embed = Embed(
            title='Discord Activity',
            description=f'[{content["JOIN_TEXT"]}](https://discord.com/invite/{code})\n\n'
                        f'**Activity:** `{activity}`',
            color=self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(
            text=content['REQUESTED_BY_TEXT'].format(ctx.author.name),
            icon_url=ctx.author.avatar_url
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @staticmethod
    def _get_data(application_id: int):
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
        description='Random item in Phasmophobia'
    )
    @is_enabled()
    async def phasmophobia_random_item(self, ctx: SlashContext):
        await self._start_random(ctx)

    @slash_subcommand(
        base='phasmo',
        name='map',
        description='Random map in Phasmophobia'
    )
    @is_enabled()
    async def phasmophobia_random_map(self, ctx: SlashContext):
        maps_list = [
            'Bleasdale Farmhouse',
            'Edgefield Street House',
            'Grafton Farmhouse',
            'Ridgeview Road House',
            'Tanglewood Street House',
            'Willow Street House',
            'Maple Lodge Campsite',
            'Brownstone High School',
            'Prison',
            'Asylum'
        ]
        await self._start_random(ctx, maps_list)

    @slash_subcommand(
        base='fun',
        name='random_item',
        description='Random item. To split your items use `,`'
    )
    @is_enabled()
    async def fun_random_item(self, ctx: SlashContext, items: str):
        pre_items_list = ''.join(items.split(' ')).split(',')
        items_list = [item for item in pre_items_list if item]

        if not items_list:
            return await ctx.send('Empty list', hidden=True)
        await self._start_random(ctx, items_list)

    async def _start_random(self, ctx: SlashContext, _list: list = None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_RANDOM_ITEMS', lang)
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
        embed = Embed(title=content['EMBED_TITLE'], color=self.bot.get_embed_color(ctx.guild_id))

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

    @slash_subcommand(
        base='fun',
        name='bored',
        description='Are you bored? Run this command and find activity for you!',
        options=[
            create_option(
                name='type',
                option_type=3,
                required=False,
                description=f'Types: {", ".join([bored_type for bored_type in bored_api_types])}',
                choices=[create_choice(name=bored_type, value=bored_type) for bored_type in bored_api_types]
            )
        ]
    )
    @is_enabled()
    async def bored_api(self, ctx: SlashContext, type: str = None):
        await ctx.defer()
        if type:
            url = f'https://www.boredapi.com/api/activity?type={type}'
        else:
            url = 'https://www.boredapi.com/api/activity'

        data = await self.bot.async_request(url)
        activity = data['activity']
        embed = Embed(
            title='You bored?',
            color=self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow()
        )
        embed.description = f'**Activity for you: ** \n{activity}\n\n**Activity type: ** `{type or data["type"]}`\n'
        embed.description += f'**Link:** {data["link"]}' if data.get('link') else ''
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @slash_subcommand(
        base='fun',
        name='calculator',
        description='Open calculator (based on calculator by Polsulpicien#5020)'
    )
    @is_enabled()
    async def start_calculator(self, ctx: SlashContext):
        calculator = Calculator(self.bot)
        await calculator.start(ctx)
