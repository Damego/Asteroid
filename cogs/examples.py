# This Cog maded to discord-components server
import asyncio
from discord.ext.commands import Cog
from discord import Embed
from discord_slash import (
    SlashContext
)
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand
)
from discord_components import Button, ButtonStyle, Select, SelectOption
from discord_slash_components_bridge import ComponentMessage, ComponentContext


from my_utils import AsteroidBot
from .settings import guild_ids



class Examples(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.name = 'examples'


    @slash_subcommand(
        base='example',
        name='button',
        description='Buttons example',
        guild_ids=guild_ids
    )
    async def button_example(self, ctx: SlashContext):
        components = [
            [
                Button(label='Blue', style=ButtonStyle.blue, custom_id='blue'),
                Button(label='Red', style=ButtonStyle.red, custom_id='red'),
                Button(label='Green', style=ButtonStyle.green, custom_id='green'),
                Button(label='Gray', style=ButtonStyle.gray, custom_id='gray'),
                Button(label='Link', style=ButtonStyle.URL, url='https://github.com/kiki7000/discord.py-components')
            ]
        ]

        message = await ctx.send('Buttons!', components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'button_click',
                    check=lambda inter: inter.message.id == message.id,
                    timeout=180
                    )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(components=components)
            
            await interaction.send(f'You clicked `{interaction.custom_id}` button', hidden=True)



    @slash_subcommand(
        base='code',
        name='button',
        description='Code of button example',
        guild_ids=guild_ids
    )
    async def button_code_example(self, ctx: SlashContext):
        code_content = """
        ```py
components = [
    [
        Button(label='Blue', style=ButtonStyle.blue, custom_id='blue'),
        Button(label='Red', style=ButtonStyle.red, custom_id='red'),
        Button(label='Green', style=ButtonStyle.green, custom_id='green'),
        Button(label='Gray', style=ButtonStyle.gray, custom_id='gray'),
        Button(label='Link', style=ButtonStyle.URL, url='https://github.com/kiki7000/discord.py-components')
    ]
]

message = await ctx.send('Buttons!', components=components)

while True:
    try:
        interaction = await self.bot.wait_for(
            'button_click',
            check=lambda inter: inter.message.id == message.id,
            timeout=180
            )
    except asyncio.TimeoutError:
        for row in components:
            row.disable_components()
        return await message.edit(components=components)
    
    await interaction.send(f'You clicked `{interaction.custom_id}` button')
        ```
        """

        await ctx.send(code_content)


    @slash_subcommand(
        base='example',
        name='select',
        description='Select example',
        guild_ids=guild_ids
    )
    async def select_example(self, ctx: SlashContext):
        components = [
            [
                Select(
                    placeholder='Select something!',
                    options=[
                        SelectOption(label='Option 1', value='option_1', emoji='1️⃣'),
                        SelectOption(label='Option 2', value='option_2', emoji='2️⃣'),
                        SelectOption(label='Option 3', value='option_3', emoji='3️⃣')
                    ],
                    min_values=1,
                    max_values=3
                )
            ]
        ]

        message = await ctx.send('Select!', components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'select_option',
                    check=lambda inter: inter.message.id == message.id,
                    timeout=180
                    )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(components=components)
            
            await interaction.send(f'You selected `{", ".join(interaction.values)}`!', hidden=True)


    @slash_subcommand(
        base='code',
        name='select',
        description='Code of select example',
        guild_ids=guild_ids
    )
    async def select_code_example(self, ctx: SlashContext):
        code_content = """
        ```py
components = [
    [
        Select(
            placeholder='Select something!',
            options=[
                SelectOption(label='Option 1', value='option_1', emoji='1️⃣'),
                SelectOption(label='Option 2', value='option_2', emoji='2️⃣'),
                SelectOption(label='Option 3', value='option_3', emoji='3️⃣')
            ],
            min_values=1,
            max_values=3
        )
    ]
]

message = await ctx.send('Select!', components=components)

while True:
    try:
        interaction = await self.bot.wait_for(
            'select_option',
            check=lambda inter: inter.message.id == message.id,
            timeout=180
            )
    except asyncio.TimeoutError:
        for row in components:
            row.disable_components()
        return await message.edit(components=components)
    
    await interaction.send(f'You selected `{interaction.values}`!', hidden=True)
        ```
        """

        await ctx.send(code_content)


    @slash_subcommand(
        base='example',
        name='button_and_select',
        description='Buttons and Select example',
        guild_ids=guild_ids
    )
    async def button_button_example(self, ctx: SlashContext):
        components = [
            [
                Select(
                    placeholder='Select something!',
                    options=[
                        SelectOption(label='Option 1', value='option_1', emoji='1️⃣'),
                        SelectOption(label='Option 2', value='option_2', emoji='2️⃣'),
                        SelectOption(label='Option 3', value='option_3', emoji='3️⃣')
                    ],
                    min_values=1,
                    max_values=3
                )
            ],
            [
                Button(label='Blue', style=ButtonStyle.blue, custom_id='blue'),
                Button(label='Red', style=ButtonStyle.red, custom_id='red'),
                Button(label='Green', style=ButtonStyle.green, custom_id='green'),
                Button(label='Gray', style=ButtonStyle.gray, custom_id='gray'),
                Button(label='Link', style=ButtonStyle.URL, url='https://github.com/kiki7000/discord.py-components')
            ]
        ]

        message = await ctx.send('Buttons and Select!', components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'component',
                    check=lambda inter: inter.message.id == message.id,
                    timeout=180
                    )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(components=components)

            if isinstance(interaction.component, Select):
                await interaction.send(f'You selected `{", ".join(interaction.values)}`!', hidden=True)
            else:
                await interaction.send(f'You clicked `{interaction.custom_id}` button', hidden=True)


    @slash_subcommand(
        base='code',
        name='button_and_select',
        description='Code of button and select example',
        guild_ids=guild_ids
    )
    async def button_select_code_example(self, ctx: SlashContext):
        code_content = """
        ```py
components = [
    [
        Select(
            placeholder='Select something!',
            options=[
                SelectOption(label='Option 1', value='option_1', emoji='1️⃣'),
                SelectOption(label='Option 2', value='option_2', emoji='2️⃣'),
                SelectOption(label='Option 3', value='option_3', emoji='3️⃣')
            ]
        )
    ],
    [
        Button(label='Blue', style=ButtonStyle.blue, custom_id='blue'),
        Button(label='Red', style=ButtonStyle.red, custom_id='red'),
        Button(label='Green', style=ButtonStyle.green, custom_id='green'),
        Button(label='Gray', style=ButtonStyle.gray, custom_id='gray'),
        Button(label='Link', style=ButtonStyle.URL, url='https://github.com/kiki7000/discord.py-components')
    ]
]

message = await ctx.send('Buttons and Select!', components=components)

while True:
    try:
        interaction = await self.bot.wait_for(
            'interaction',
            check=lambda inter: inter.message.id == message.id,
            timeout=180
            )
    except asyncio.TimeoutError:
        for row in components:
            row.disable_components()
        return await message.edit(components=components)

    if isinstance(interaction.component, Select):
        await interaction.send(f'You selected `{", ".join(interaction.values)}`!')
    else:
        await interaction.send(f'You clicked `{interaction.custom_id}` button')
        ```
        """

        await ctx.send(code_content)


def setup(bot):
    bot.add_cog(Examples(bot))