# This Cog maded to discord-components server
import asyncio
from discord.ext.commands import Cog
from discord_slash import (
    SlashContext
)
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_components import Button, ButtonStyle, Select, SelectOption

from my_utils import AsteroidBot, Cog
from .settings import guild_ids



class Examples(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.name = 'Examples'
        self.emoji = '⚙️'


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
                    timeout=60
                )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(content='Timed out!', components=components)
            
            await interaction.send(f'You clicked `{interaction.custom_id}` button', hidden=True)



    @slash_subcommand(
        base='code',
        name='button',
        description='Code of button example',
        guild_ids=guild_ids,
        options=[
            create_option(
                name='type',
                description='Type of code',
                option_type=3,
                required=True,
                choices=[
                    create_choice(
                        name='event',
                        value='event'
                    ),
                    create_choice(
                        name='wait_for',
                        value='wait_for'
                    ),
                    create_choice(
                        name='callback',
                        value='callback'
                    )
                ]
            )
        ]
    )
    async def button_code_example(self, ctx: SlashContext, type: str):
        if type == 'wait_for':
            code_content = """
            ```py
@commands.command()
async def button(self, ctx):
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
                timeout=60
            )
        except asyncio.TimeoutError:
            for row in components:
                row.disable_components()
            return await message.edit(content='Timed out!', components=components)
        
        await interaction.send(f'You clicked `{interaction.custom_id}` button')
```"""
        elif type == 'event':
            code_content = """
            ```py
@commands.command()
async def button(self, ctx):
    components = [
        [
            Button(label='Blue', style=ButtonStyle.blue, custom_id='blue'),
            Button(label='Red', style=ButtonStyle.red, custom_id='red'),
            Button(label='Green', style=ButtonStyle.green, custom_id='green'),
            Button(label='Gray', style=ButtonStyle.gray, custom_id='gray'),
            Button(label='Link', style=ButtonStyle.URL, url='https://github.com/kiki7000/discord.py-components')
        ]
    ]

    await ctx.send('Buttons!', components=components)

@commands.Cog.listener()
async def on_button_click(self, interaction):
    await interaction.send(f'You clicked `{interaction.custom_id}` button')
```"""
        else:
            code_content = """
            ```py
@commands.command()
async def button(self, ctx):
    components = [
        [
            self.bot.components_manager.add_callback(
                Button(label='Click Me!', style=ButtonStyle.blue, custom_id='callback_button'),
                self.callback
            )
        ]
    ]

    await ctx.send('Buttons!', components=components)

async def callback(self, interaction):
    await interaction.send(f'You clicked callback button!')
```"""
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
                    timeout=60
                )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(content='Timed out!', components=components)
            
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
@commands.command()
async def select(self, ctx):
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
                timeout=60
            )
        except asyncio.TimeoutError:
            for row in components:
                row.disable_components()
            return await message.edit(content='Timed out!', components=components)
        
        await interaction.send(f'You selected `{interaction.values}`!')
        ```"""
        
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
                    timeout=60
                )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(content='Timed out!', components=components)

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
@commands.command()
async def select_and_buttons(self, ctx):
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
                timeout=60
            )
        except asyncio.TimeoutError:
            for row in components:
                row.disable_components()
            return await message.edit(content='Timed out!', components=components)

        if isinstance(interaction.component, Select):
            await interaction.send(f'You selected `{", ".join(interaction.values)}`!')
        else:
            await interaction.send(f'You clicked `{interaction.custom_id}` button')
        ```"""

        await ctx.send(code_content)


    @slash_subcommand(
        base='example',
        name='private1',
        description='Private button example 1 (Shows This interaction failed for others)',
        guild_ids=guild_ids
    )
    async def private_button_example1(self, ctx: SlashContext):
        count = 0
        components = [
            [
                Button(label=count, style=ButtonStyle.blue)
            ]
        ]

        message = await ctx.send(f'Only {ctx.author} can click this button', components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'button_click',
                    check=lambda inter: inter.message.id == message.id and inter.author_id == ctx.author_id,
                    timeout=60
                )
            except asyncio.TimeoutError:
                components[0][0].label = f'{count}'
                for row in components:
                    row.disable_components()
                return await message.edit(content='Timed out!', components=components)

            count += 1
            interaction.component.label = count
            await interaction.edit_origin(components=interaction.message.components)



    @slash_subcommand(
        base='code',
        name='private1',
        description='Code of Private button example 1',
        guild_ids=guild_ids
    )
    async def private_button_code_example1(self, ctx: SlashContext):
        code_content = """
        ```py
@commands.command()
async def private_button1(self, ctx):
    count = 0
    components = [
        [
            Button(label=count, style=ButtonStyle.blue)
        ]
    ]

    message = await ctx.send(f'Only {ctx.author} can click this button', components=components)

    while True:
        try:
            interaction = await self.bot.wait_for(
                'button_click',
                check=lambda inter: inter.message.id == message.id and inter.author.id == ctx.author.id,
                timeout=60
            )
        except asyncio.TimeoutError:
            components[0][0].label = f'{count}'
            for row in components:
                row.disable_components()
            return await message.edit(content='Timed out!', components=components)

        count += 1
        interaction.component.label = count
        await interaction.edit_origin(components=interaction.message.components)
        ```"""

        await ctx.send(code_content)


    @slash_subcommand(
        base='example',
        name='private2',
        description='Private button example 2',
        guild_ids=guild_ids
    )
    async def private_button_example2(self, ctx: SlashContext):
        count = 0
        components = [
            [
                Button(label=count, style=ButtonStyle.blue)
            ]
        ]

        message = await ctx.send(f'Only {ctx.author} can click this button', components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'button_click',
                    check=lambda inter: inter.message.id == message.id,
                    timeout=60
                )
            except asyncio.TimeoutError:
                components[0][0].label = f'{count}'
                for row in components:
                    row.disable_components()
                return await message.edit(content='Timed out!', components=components)

            if interaction.author_id == ctx.author_id:
                count += 1
                interaction.component.label = count
                await interaction.edit_origin(components=interaction.message.components)
            else:
                await interaction.send('Hey! You can\'t interact with this button!', hidden=True)


    @slash_subcommand(
        base='code',
        name='private2',
        description='Code of Private button example 2',
        guild_ids=guild_ids
    )
    async def private_button_code_example2(self, ctx: SlashContext):
        code_content = """
        ```py
@commands.command()
async def private_button2(self, ctx):
    count = 0
    components = [
        [
            Button(label=count, style=ButtonStyle.blue)
        ]
    ]

    message = await ctx.send(f'Only {ctx.author} can click this button', components=components)

    while True:
        try:
            interaction = await self.bot.wait_for(
                'button_click',
                check=lambda inter: inter.message.id == message.id,
                timeout=60
            )
        except asyncio.TimeoutError:
            components[0][0].label = f'{count}'
            for row in components:
                row.disable_components()
            return await message.edit(content='Timed out!', components=components)
        
        if interaction.author.id == ctx.author.id:
            count += 1
            interaction.component.label = count
            await interaction.edit_origin(components=interaction.message.components)
        else:
            await interaction.send('Hey! You can\'t interact with this button!')
        ```"""

        await ctx.send(code_content)

    @slash_subcommand(
        base='example',
        name='check_by_custom_id',
        description='You can check what button was pressed',
        guild_ids=guild_ids
    )
    async def check_custom_id(self, ctx: SlashContext):
        components = [
            [
                Button(label='Button 1', style=ButtonStyle.blue, custom_id='button_1'),
                Button(label='Button 2', style=ButtonStyle.blue, custom_id='button_2'),
                Button(label='Button 3', style=ButtonStyle.blue, custom_id='button_3'),
            ]
        ]

        message = await ctx.send('Check by custom id', components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'button_click',
                    check=lambda inter: inter.message.id == message.id,
                    timeout=60
                )
            except asyncio.TimeoutError:
                for row in components:
                    row.disable_components()
                return await message.edit(content='Timed out!', components=components)

            if interaction.custom_id == 'button_1':
                await interaction.send('Hey! Whats up?', hidden=True)
            elif interaction.custom_id == 'button_2':
                await interaction.send('Wow! You clicked `Button 2`', hidden=True)
            elif interaction.custom_id == 'button_3':
                await interaction.send('lmao', hidden=True)


    @slash_subcommand(
        base='code',
        name='check_by_custom_id',
        description='Code of check_by_custom_id example',
        guild_ids=guild_ids
    )
    async def code_check_custom_id_example(self, ctx: SlashContext):
        code_content = """
        ```py
@commands.command()
async def check_custom_id(self, ctx):
    components = [
        [
            Button(label='Button 1', style=ButtonStyle.blue, custom_id='button_1'),
            Button(label='Button 2', style=ButtonStyle.blue, custom_id='button_2'),
            Button(label='Button 3', style=ButtonStyle.blue, custom_id='button_3'),
        ]
    ]

    message = await ctx.send('Check by custom id', components=components)

    while True:
        try:
            interaction = await self.bot.wait_for(
                'button_click',
                check=lambda inter: inter.message.id == message.id,
                timeout=60
            )
        except asyncio.TimeoutError:
            for row in components:
                row.disable_components()
            return await message.edit(content='Timed out!', components=components)

        if interaction.custom_id == 'button_1':
            await interaction.send('Hey! Whats up?')
        elif interaction.custom_id == 'button_2':
            await interaction.send('Wow! You clicked `Button 2`')
        elif interaction.custom_id == 'button_3':
            await interaction.send('lmao')
        ```"""

        await ctx.send(code_content)



def setup(bot):
    bot.add_cog(Examples(bot))