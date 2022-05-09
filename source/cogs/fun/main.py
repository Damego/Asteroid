import json
from asyncio import TimeoutError
from datetime import datetime
from os import environ, remove
from random import choice, randint

import qrcode
import requests
from aiohttp import ClientSession
from discord import ChannelType, Embed, File, Forbidden, Member, VoiceChannel
from discord_slash import (
    Button,
    ButtonStyle,
    ComponentContext,
    Select,
    SelectOption,
    SlashCommandOptionType,
    SlashContext,
)
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import AsteroidBot, Cog, consts, get_content, is_enabled

from .game_consts import bored_api_types, discord_activities_list
from .games import (
    BoardMode,
    Calculator,
    MonkeyMemory,
    Pairs,
    RockPaperScissors,
    TicTacToeAI,
    TicTacToeMode,
    TicTacToeOnline,
    Tiles,
)


class Fun(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.name = "Fun"
        self.emoji = "🎮"

    @slash_subcommand(
        base="game",
        name="rps",
        description="Start play a Rock Paper Scissors",
        base_dm_permission=False,
        options=[
            create_option(
                name="member",
                description="Member you want to invite (Also bots)",
                option_type=SlashCommandOptionType.USER,
            ),
            create_option(
                name="total_rounds",
                description="Max rounds you want to play",
                option_type=SlashCommandOptionType.INTEGER,
                min_value=1,
                max_value=100,
                required=False,
            ),
        ],
    )
    @is_enabled()
    async def rockpaperscissors_cmd(self, ctx: SlashContext, member: Member, total_rounds: int = 3):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("FUNC_INVITE_TO_GAME", lang)

        if member.id == ctx.author_id:
            return await ctx.send(content["SELF_INVITE"])

        game_name = get_content("GAMES_NAMES", lang)["RPS"]
        message, accept = await self.invite_to_game(ctx, member, game_name)

        if not accept:
            return

        game = RockPaperScissors(self.bot, ctx, member, message, total_rounds)
        await game.start_game()

    @slash_subcommand(
        base="game",
        subcommand_group="ttt",
        name="online",
        description="Play a TicTacToe game Online",
        options=[
            create_option(
                name="member",
                description="Whoever you want to play with",
                required=True,
                option_type=SlashCommandOptionType.USER,
            ),
            create_option(
                name="mode",
                description="Choose mode of game (3x3, 4x4, 5x5)",
                required=False,
                option_type=SlashCommandOptionType.STRING,
                choices=[
                    create_choice(name="3x3", value="3x3"),
                    create_choice(name="4x4", value="4x4"),
                    create_choice(name="5x5", value="5x5"),
                ],
            ),
        ],
    )
    @is_enabled()
    async def tictactoe_cmd(self, ctx: SlashContext, member: Member, mode: str = "3x3"):
        await self.start_tictactoe_online(ctx, member, mode)

    @slash_subcommand(
        base="game",
        subcommand_group="ttt",
        name="bot",
        description="Play a TicTacToe game with bot!",
    )
    @is_enabled()
    async def ttt_game_ai(self, ctx: SlashContext):
        components = [
            [
                Button(label="Easy", style=ButtonStyle.blue, custom_id="ttt_easy"),
                Button(label="Impossible", style=ButtonStyle.blue, custom_id="ttt_imp"),
            ]
        ]
        embed = Embed(
            title="Tic Tac Toe Game",
            description="**Choose a difficult:**"
            "\n`Easy` - Bot random clicks on free cell"
            "\n`Impossible` - Bot with minimax AI.",
            color=await self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        message = await ctx.send(embed=embed, components=components)

        try:
            button_ctx: ComponentContext = await self.bot.wait_for(
                "button_click",
                check=lambda __ctx: __ctx.author_id == ctx.author_id
                and __ctx.origin_message.id == message.id,
                timeout=60,
            )
        except TimeoutError:
            return await message.delete()

        if button_ctx.custom_id == "ttt_easy":
            mode = TicTacToeMode.easy
        else:
            mode = TicTacToeMode.impossible

        ttt = TicTacToeAI(self.bot, button_ctx, mode=mode)
        await ttt.start(edit_origin=True, message=message)

    async def start_tictactoe_online(self, ctx, member: Member, mode: str):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        invite_content = get_content("FUNC_INVITE_TO_GAME", lang)
        game_content = get_content("GAME_TTT", lang)
        game_name = get_content("GAMES_NAMES", lang)["TTT"]

        if member.id == ctx.author_id:
            return await ctx.send(invite_content["SELF_INVITE"])
        if member.bot:
            return await ctx.send(invite_content["BOT_INVITE"])

        message, accept = await self.invite_to_game(ctx, member, game_name)
        if not accept:
            return

        if mode == "3x3":
            board_mode = BoardMode.x3
        elif mode == "4x4":
            board_mode = BoardMode.x4
        elif mode == "5x5":
            board_mode = BoardMode.x5

        game = TicTacToeOnline(self.bot, message, ctx, member, game_content, board_mode)
        await game.start_game()

    async def invite_to_game(self, ctx, member, game_name):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("FUNC_INVITE_TO_GAME", lang)
        button_label_agree = content["BUTTON_AGREE"]
        button_label_decline = content["BUTTON_DECLINE"]
        invite_text = content["INVITE_MESSAGE_CONTENT"].format(
            member.mention, ctx.author.name, game_name
        )
        components = [
            [
                Button(style=ButtonStyle.green, label=button_label_agree, custom_id="agree"),
                Button(
                    style=ButtonStyle.red,
                    label=button_label_decline,
                    custom_id="decline",
                ),
            ]
        ]

        message = await ctx.send(content=invite_text, components=components)

        if member.bot:
            embed = Embed(
                title=game_name,
                description=f"{ctx.author.display_name} VS {member.display_name}",
                color=await self.bot.get_embed_color(ctx.guild.id),
            )
            await message.edit(content=" ", embed=embed)
            return message, True

        try:
            button_ctx: ComponentContext = await self.bot.wait_for(
                "button_click",
                check=lambda _ctx: _ctx.author_id == member.id,
                timeout=60,
            )
            accepted_invite = content["AGREE_MESSAGE_CONTENT"]
            await button_ctx.send(accepted_invite, hidden=True)
        except TimeoutError:
            timeout_error = content["TIMEOUT_MESSAGE_CONTENT"].format(member.display_name)
            await message.edit(content=timeout_error, components=[])
            return message, False

        if button_ctx.custom_id == "agree":
            embed = Embed(
                title=game_name,
                description=f"{ctx.author.display_name} VS {member.display_name}",
                color=await self.bot.get_embed_color(ctx.guild.id),
            )
            await message.edit(content=" ", embed=embed)
            return message, True

        declined_invite = content["DECLINE_MESSAGE_CONTENT"].format(member.display_name)
        await message.edit(content=declined_invite, components=[])
        return message, False

    @slash_subcommand(
        base="fun",
        name="random_num",
        description="Generate random number",
        base_dm_permission=False,
    )
    @is_enabled()
    async def random_num(self, ctx: SlashContext, start: int, end: int):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("FUNC_RANDOM_NUMBER_OUT_CONTENT", lang)

        random_number = randint(start, end)
        await ctx.reply(content.format(random_number))

    @slash_subcommand(base="fun", name="qr", description="Create a QR-code")
    @is_enabled()
    async def create_qr(self, ctx: SlashContext, text: str):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(data=text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"./qrcodes/{ctx.author.id}.png")
        await ctx.send(file=File(f"./qrcodes/{ctx.author.id}.png"))
        remove(f"./qrcodes/{ctx.author.id}.png")

    @slash_subcommand(
        base="fun",
        name="activity",
        description="Open discord Activities",
        options=[
            create_option(
                name="activity",
                description="Choose discord activity",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                choices=[
                    create_choice(name=activity, value=activity)
                    for activity in discord_activities_list
                ],
            ),
            create_option(
                name="channel",
                description="Choose voice channel",
                required=False,
                option_type=SlashCommandOptionType.CHANNEL,
                channel_types=[ChannelType.voice],
            ),
        ],
    )
    @is_enabled()
    async def start_activity(self, ctx: SlashContext, activity: str, channel: VoiceChannel = None):
        await ctx.defer()
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("FUNC_ACTIVITIES", lang=lang)

        if not channel and not ctx.author.voice:
            return await ctx.send(content["NOT_CONNECTED_TO_CHANNEL_TEXT"])
        if channel and not isinstance(channel, VoiceChannel):
            return await ctx.send(content["WRONG_CHANNEL_TEXT"])
        if not channel:
            channel = ctx.author.voice.channel

        code = await self._get_invite_code(channel.id, activity)
        if code == "50013":
            raise Forbidden

        embed = Embed(
            title="Discord Activity",
            description=f'[{content["JOIN_TEXT"]}](https://discord.com/invite/{code})\n\n'
            f"**Activity:** `{activity}`",
            color=await self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(
            text=content["REQUESTED_BY_TEXT"].format(ctx.author.name),
            icon_url=ctx.author.avatar_url,
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        await ctx.send(embed=embed)

    async def _get_invite_code(self, channel_id: int, activity: str):
        data = {
            "max_age": 86400,
            "max_uses": 0,
            "target_application_id": int(discord_activities_list[activity]),
            "target_type": 2,
            "temporary": False,
            "validate": None,
        }
        headers = {
            "Authorization": f'Bot {environ.get("BOT_TOKEN")}',
            "Content-Type": "application/json",
        }

        async with ClientSession() as client:
            async with client.post(
                f"https://discord.com/api/v10/channels/{channel_id}/invites",
                data=json.dumps(data),
                headers=headers,
            ) as response:
                json_response = await response.json()
                code = json_response["code"]

        return code

    @slash_subcommand(
        base="phasmo",
        name="item",
        description="Random item in Phasmophobia",
        base_dm_permission=False,
    )
    @is_enabled()
    async def phasmophobia_random_item(self, ctx: SlashContext):
        await self._start_random(ctx)

    @slash_subcommand(base="phasmo", name="map", description="Random map in Phasmophobia")
    @is_enabled()
    async def phasmophobia_random_map(self, ctx: SlashContext):
        maps_list = [
            "Bleasdale Farmhouse",
            "Edgefield Street House",
            "Grafton Farmhouse",
            "Ridgeview Road House",
            "Tanglewood Street House",
            "Willow Street House",
            "Maple Lodge Campsite",
            "Brownstone High School",
            "Prison",
            "Asylum",
        ]
        await self._start_random(ctx, maps_list)

    @slash_subcommand(
        base="fun",
        name="random_item",
        description="Random item. To split your items use `,`",
    )
    @is_enabled()
    async def fun_random_item(self, ctx: SlashContext, items: str):
        pre_items_list = "".join(items.split(" ")).split(",")
        items_list = [item for item in pre_items_list if item]

        if not items_list:
            return await ctx.send("Empty list", hidden=True)
        await self._start_random(ctx, items_list)

    async def _start_random(self, ctx: SlashContext, _list: list = None):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("FUNC_RANDOM_ITEMS", lang)
        if _list is None:
            _list = content["ITEMS_LIST"]
        components = [
            Button(
                style=ButtonStyle.blue,
                label=content["SELECT_BUTTON"],
                custom_id="toggle",
            ),
            Select(
                placeholder=content["SELECT_ITEMS_TEXT"],
                options=[SelectOption(label=item, value=item) for item in _list],
                max_values=len(_list),
            ),
            [
                Button(
                    label=content["START_RANDOM_BUTTON"],
                    custom_id="start_random",
                    style=ButtonStyle.green,
                ),
                Button(
                    label=content["EXIT_BUTTON"],
                    custom_id="exit",
                    style=ButtonStyle.red,
                ),
            ],
        ]
        selected = None
        is_exception = False
        is_removed = False
        embed = Embed(
            title=content["EMBED_TITLE"],
            color=await self.bot.get_embed_color(ctx.guild_id),
        )

        message = await ctx.send(embed=embed, components=components)
        message_for_update = await ctx.send(content["SECOND_MESSAGE_CONTENT"])

        while True:
            try:
                button_ctx = await self._get_button_ctx(ctx, message, message_for_update)
            except TimeoutError:
                return

            if isinstance(button_ctx.component, Select):
                selected = button_ctx.values
                if is_exception:
                    _selected = _list.copy()
                    for item in selected:
                        _selected.remove(item)
                    selected = _selected
                embed.description = content["SELECTED_ITEMS_TEXT"] + ", ".join(selected)
                await button_ctx.edit_origin(embed=embed)

            elif button_ctx.custom_id == "toggle":
                is_exception = not is_exception
                button_ctx.component.label = (
                    content["EXCEPTION_BUTTON"] if is_exception else content["SELECT_BUTTON"]
                )
                selected = None
                is_removed = False
                embed.description = ""

                await button_ctx.edit_origin(
                    embed=embed, components=button_ctx.origin_message.components
                )

            elif button_ctx.custom_id == "start_random":
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

            elif button_ctx.custom_id == "exit":
                await message.delete()
                await message_for_update.delete()
                return

    async def _get_button_ctx(self, ctx: SlashContext, message, message_for_update):
        try:
            button_ctx: ComponentContext = await self.bot.wait_for(
                "component",
                check=lambda _ctx: _ctx.author_id == ctx.author_id
                and _ctx.origin_message_id == message.id,
                timeout=3600,
            )
        except TimeoutError as te:
            await message.delete()
            await message_for_update.delete()
            raise TimeoutError from te
        else:
            await button_ctx.defer(edit_origin=True)
            return button_ctx

    @slash_subcommand(
        base="fun",
        name="bored",
        description="Are you bored? Run this command and find activity for you!",
        options=[
            create_option(
                name="type",
                option_type=SlashCommandOptionType.STRING,
                required=False,
                description=f'Types: {", ".join([bored_type for bored_type in bored_api_types])}',
                choices=[
                    create_choice(name=bored_type, value=bored_type)
                    for bored_type in bored_api_types
                ],
            )
        ],
    )
    @is_enabled()
    async def bored_api(self, ctx: SlashContext, type: str = None):
        await ctx.defer()
        if type:
            url = f"https://www.boredapi.com/api/activity?type={type}"
        else:
            url = "https://www.boredapi.com/api/activity"

        data = await self.bot.async_request(url)
        activity = data["activity"]
        embed = Embed(
            title="You bored?",
            color=await self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.utcnow(),
        )
        embed.description = (
            f'**Activity for you: ** \n{activity}\n\n**Activity type: ** `{type or data["type"]}`\n'
        )
        embed.description += f'**Link:** {data["link"]}' if data.get("link") else ""
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @slash_subcommand(
        base="fun",
        name="calculator",
        description="Open calculator (based on calculator by Polsulpicien#5020)",
    )
    @is_enabled()
    async def start_calculator(self, ctx: SlashContext):
        calculator = Calculator(self.bot)
        await calculator.start(ctx)

    @slash_subcommand(
        base="game",
        name="monkeymemory",
        description="Start game Monkey Memory",
        options=[
            create_option(
                name="timeout",
                description="The time to remember (in seconds). Default of 5 seconds.",
                option_type=SlashCommandOptionType.INTEGER,
                required=False,
                min_value=1,
                max_value=60,
            )
        ],
    )
    @is_enabled()
    async def start_mm(self, ctx: SlashContext, timeout: int = 5):
        game = MonkeyMemory(ctx, timeout)
        await game.start()

    @slash_subcommand(base="game", name="tiles", description="Start game tiles")
    @is_enabled()
    async def start_tiles(self, ctx: SlashContext):
        game = Tiles(ctx)
        await game.start()

    @slash_subcommand(base="game", name="pairs", description="Start a game Pairs")
    @is_enabled()
    async def start_pairs(self, ctx: SlashContext, is_hardcore: bool = False):
        if is_hardcore:
            cards = ["🇦🇨", "🇦🇮", "🇦🇺", "🇨🇰", "🇫🇰", "🇬🇸", "🇰🇾", "🇲🇸", "🇳🇿", "🇹🇦", "🇹🇨", "🇻🇬"]
            pairs = Pairs(ctx, cards=cards)
        else:
            pairs = Pairs(ctx)
        await pairs.start()
