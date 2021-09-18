from asyncio import TimeoutError

import discord
from discord_components import Button, ButtonStyle
from discord.ext import commands

from ._tictactoe import TicTacToe
from ._rockpaperscissors import RockPaperScissors



class Games(commands.Cog, description='Games'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🎮'


    @commands.command(aliases=['rps'], description='Start game Rock Paper Scissors', help='(User) (total games)')
    async def rockpaperscissors(self, ctx: commands.Context, member: discord.Member=None, total_rounds: int=3):
        if member is None:
            member = ctx.bot.user
        if member == ctx.author:
            await ctx.send('You cannot invite yourself!')
            return

        msg, accept = await self.invite_to_game(ctx, member, 'Rock Paper Scissors')

        if not accept:
            return

        game = RockPaperScissors(self.bot, ctx, member, msg, total_rounds)
        await game.start_game()


    @commands.command(aliases=['ttt'], description='Start game Tic Tac Toe', help='[User]')
    async def tictactoe(self, ctx:commands.Context, member: discord.Member):
        if member == ctx.author:
            await ctx.send('You cannot invite yourself!')
            return
        if member.bot:
            await ctx.send('You cannot invite bot!')
            return
        msg, accept = await self.invite_to_game(ctx, member, 'Tic Tac Toe')
        if not accept:
            return

        game = TicTacToe(self.bot, msg, ctx, member)
        await game.start_game()


#    @commands.group(name='blackjack', description='Start game BlackJack', help='', invoke_without_command=True)
#    async def blackjack(self, ctx:commands.Context):
#        start_menu_components = [[
#                Button(style=ButtonStyle.green, label='Start game', id='start_game'),
#                Button(style=ButtonStyle.red, label='Exit', id='exit_game'),
#            ]]
#
#        msg = await ctx.send(content='BlackJack', components=start_menu_components)
#
#        interaction = await self.bot.wait_for('button_click', check=lambda i: i.user.id == ctx.author.id)
#        await interaction.respond(type=6)
#
#        if interaction.component.id == 'exit_game':
#            await msg.delete()
#            return
#        blackjack = BlackJack(self.bot)
#        await blackjack.prepare_for_game(ctx, msg)


    async def invite_to_game(self, ctx, member, game_name):
        def member_agree(interaction):
            return interaction.user.id == member.id and interaction.message.id == message.id

        message = await ctx.send(
            content=f"{member.mention}! {ctx.author.name} invites you in {game_name}",
            components=[
                [
                    Button(style=ButtonStyle.green, label='Agree', id='agree'),
                    Button(style=ButtonStyle.red, label='Decline', id='decline')
                ]])
        if member.bot:
            embed = discord.Embed(
                title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}', color=self.bot.get_embed_color(ctx.guild.id))
            await message.edit(context=' ', embed=embed)
            return message, True
            
        try:
            interaction = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
            await interaction.respond(type=6)
        except TimeoutError:
            await message.edit(content=f'No response from {member.display_name}!', components=[])
            return message, False

        if interaction.component.id == 'agree':
            embed = discord.Embed(
                title=game_name, description=f'{ctx.author.display_name} VS {member.display_name}', color=self.bot.get_embed_color(ctx.guild.id))
            await message.edit(context=' ', embed=embed)
            return message, True

        await message.edit(content=f'{member.display_name} declined invite!', components=[])
        return message, False