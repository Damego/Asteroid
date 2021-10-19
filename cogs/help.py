import asyncio
from discord import Embed
from discord.ext.commands import Cog
from discord_slash import SlashContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
)
from discord_components import Select, SelectOption

from my_utils import AsteroidBot
from .settings import guild_ids



class Help(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '💡'
        self.name = 'help'


    @slash_command(
        name='help',
        description='Show all bot\'s commands',
        guild_ids=guild_ids
    )
    async def help_command(self, ctx: SlashContext):
        commands_data = self._get_commands_data()
        components = [
            Select(
                placeholder='Select a module',
                options=[SelectOption(label=cog.capitalize(), value=cog.capitalize()) for cog in commands_data]
            )
        ]
        embeds = []
        for cog in commands_data:
            embed = Embed(title=cog.capitalize(), description='')
            for _base_command in commands_data[cog]:
                base_command = commands_data[cog][_base_command]
                for _group in base_command:
                    if _group in ['command_description', 'has_subcommmand_group', 'description']:
                        continue
                    group = base_command[_group]
                    is_group = group.get('has_subcommmand_group')
                    if is_group is None:
                        for _command_name in group:
                            if _command_name in ['command_description', 'has_subcommmand_group']:
                                continue
                            command = group[_command_name]
                            option_line = self.get_options(command)
                            embed.description += f"`/{_base_command} {_group} {_command_name} {option_line}`\n *description:* {command['description']} \n"
                    else:
                        option_line = self.get_options(group)
                        embed.description += f"`/{_base_command} {_group} {option_line}`\n *description:* {group['description']} \n"

            embeds.append(embed)

        message = await ctx.send(embed=embeds[0], components=components)

        while True:
            try:
                interaction = await self.bot.wait_for(
                    'select_option',
                    check=lambda inter: inter.author_id == ctx.author_id and inter.message.id == message.id,
                    timeout=60
                    )
            except asyncio.TimeoutError:
                components[0].disabled = True
                return await message.edit(components=components)

            value = interaction.values[0]
            for embed in embeds:
                if embed.title == value:
                    break
            await interaction.edit_origin(embed=embed)


    def get_options(self, command):
        options = command['options']
        option_line = ''
        if options is None:
            return option_line
        for _option in options:
            option_name = _option['name']
            option_line += f'[{option_name}] ' if _option['required'] else f'({option_name}) '
        return option_line


    def _get_commands_data(self):
        commands_data = {}
        _commands = self.bot.slash.commands
        for _command in _commands:
            if _command == 'context':
                continue
            command = _commands[_command]
            if command.cog.name not in commands_data:
                commands_data[command.cog.name] = {}
            commands_data[command.cog.name][_command] = {
                'command_description': command.description
            }
        self._get_subcommands_data(commands_data)
        return commands_data


    def _get_subcommands_data(self, commands_data):
        _subcommands = self.bot.slash.subcommands
        for _slash_command in _subcommands:
            command = _subcommands[_slash_command]
            for _slash_subcommand in command:
                cogsubcommand = command[_slash_subcommand]
                if isinstance(cogsubcommand, dict):
                    for _group in cogsubcommand:
                        group = cogsubcommand[_group]
                        self._append_subcommand(commands_data, group)
                else:
                    self._append_subcommand(commands_data, cogsubcommand)


    def _append_subcommand(self, commands_data, command):
        if command.cog.name not in commands_data:
            commands_data[command.cog.name] = {}
        if command.base not in commands_data[command.cog.name]:
            commands_data[command.cog.name][command.base] = {}

        has_subcomand_group = command.subcommand_group is not None
        if has_subcomand_group:
            if command.subcommand_group not in commands_data[command.cog.name][command.base]:
                commands_data[command.cog.name][command.base][command.subcommand_group] = {}
            commands_data[command.cog.name][command.base][command.subcommand_group][command.name] = {
                    'description': command.description,
                    'options': command.options
            }
        else:
            commands_data[command.cog.name][command.base][command.name] = {
                    'has_subcommmand_group': False,
                    'description': command.description,
                    'options': command.options
            }
            

def setup(bot):
    bot.add_cog(Help(bot))
