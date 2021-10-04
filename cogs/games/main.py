from asyncio import TimeoutError

import discord
from discord.ext.commands import Cog
from discord_slash import SlashContext, ButtonStyle, ContextMenuType, MenuContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu
)
from discord_slash.utils.manage_components import (
    create_button as Button,
    create_actionrow as ActionRow,
    wait_for_component
)

from ._tictactoe import TicTacToe
from ._rockpaperscissors import RockPaperScissors
from my_utils import AsteroidBot
from my_utils import get_content
from ..settings import guild_ids


class Games(Cog, description='Игры'):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot


    @slash_subcommand(
        base='game',
        name='rps',
        description='Start play a Rock Paper Scissors',
        guild_ids=guild_ids
    )
    async def rockpaperscissors_cmd(self, ctx: SlashContext, member: discord.Member, total_rounds: int=1):
        await self._start_rps(ctx, member, total_rounds)

    @context_menu(
        target=ContextMenuType.MESSAGE,
        name='Start Rock Paper Scissors',
        guild_ids=guild_ids
    )
    async def rockpaperscissors_contex(self, ctx: MenuContext):
        member = ctx.target_message.author
        await self._start_rps(ctx, member, 3)
        

    async def _start_rps(self, ctx: SlashContext, member: discord.Member, total_rounds: int=1):
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
        name='ttt',
        description='Play a Tic Tac Toe',
        guild_ids=guild_ids
    )
    async def tictactoe_cmd(self, ctx: SlashContext, member: discord.Member):
        await self._start_ttt(ctx, member)
        
    @context_menu(
        target=ContextMenuType.MESSAGE,
        name='Start Tic Tac Toe',
        guild_ids=guild_ids
    )
    async def tictactoe_cmd(self, ctx: MenuContext):
        member = ctx.target_message.author
        await self._start_ttt(ctx, member)


    async def _start_ttt(self, ctx, member: discord.Member):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_INVITE_TO_GAME', lang)
        game_name = get_content('GAMES_NAMES', lang)['TTT']

        if member.id == ctx.author_id:
            return await ctx.send(content['SELF_INVITE'])
        if member.bot:
            return await ctx.send(content['BOT_INVITE'])
            
        message, accept = await self.invite_to_game(ctx, member, game_name)
        if not accept:
            return

        game = TicTacToe(self.bot, message, ctx, member)
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
            return interaction.author.id == member.id

        components = [
            Button(style=ButtonStyle.green, label=button_label_agree, custom_id='agree'),
            Button(style=ButtonStyle.red, label=button_label_decline, custom_id='decline')
        ]
        action_row = ActionRow(*components)

        message = await ctx.send(
            content=invite_text,
            components=[ActionRow(*components)])

        if member.bot:
            embed = discord.Embed(
                title=game_name,
                description=f'{ctx.author.display_name} VS {member.display_name}',
                color=self.bot.get_embed_color(ctx.guild.id)
            )
            await message.edit(content=' ', embed=embed)
            return message, True
            
        try:
            interaction = await wait_for_component(self.bot, components=action_row, check=member_agree, timeout=60)
            accepted_invite = content['AGREE_MESSAGE_CONTENT']
            await interaction.send(accepted_invite, hidden=True)
        except TimeoutError:
            timeout_error = content['TIMEOUT_MESSAGE_CONTENT'].format(member.display_name)
            await message.edit(content=timeout_error, components=[])
            return message, False

        if interaction.custom_id == 'agree':
            embed = discord.Embed(
                title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}', color=self.bot.get_embed_color(ctx.guild.id))
            await message.edit(context=' ', embed=embed)
            return message, True

        declined_invite = content['DECLINE_MESSAGE_CONTENT'].format(member.display_name)
        await message.edit(content=declined_invite, components=[])
        return message, False