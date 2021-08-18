import asyncio
from asyncio import tasks
import discord
from discord.ext import commands
from discord_components import ButtonStyle, Button
from discord_components.component import Select, SelectOption
from discord_components.interaction import Interaction


class Tests(commands.Cog, description=''):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True

    @commands.command(
    name='test',
    description='',
    help='')
    async def test(self, ctx:commands.Context):
        components = [
            [Button(style=ButtonStyle.blue, label='test', id='1')],
            Select(
                placeholder='test',
                options=[
                    SelectOption(label='testoption', value='2')
                ]
            )
        ]

        await ctx.send('test', components=components)

        task1 = await asyncio.wait(
            [self.bot.wait_for('select_option'), self.bot.wait_for('button_click')], return_when=asyncio.FIRST_COMPLETED
        )
        print(task1)
        #await interaction.respond(interaction.component)


def setup(bot):
    bot.add_cog(Tests(bot))