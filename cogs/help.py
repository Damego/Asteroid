import asyncio

from discord import Embed
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_slash as slash_command
from discord_components import Select, SelectOption
from discord_slash_components_bridge import ComponentContext

from my_utils import AsteroidBot, get_content, Cog


class Help(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = True
        self.name = 'Help'

    @slash_command(
        name='help',
        description='Show all bot\'s commands'
    )
    async def help_command(self, ctx: SlashContext):
        components = self._init_components()
        embeds = self._init_embeds(ctx)
        message = await ctx.send(embed=embeds[0], components=components)

        while True:
            try:
                interaction: ComponentContext = await self.bot.wait_for(
                    'select_option',
                    check=lambda inter: inter.author_id == ctx.author_id and inter.message.id == message.id,
                    timeout=60
                    )
            except asyncio.TimeoutError:
                return await message.edit(components=[])

            value = interaction.values[0]

            if value == 'main_page':
                embed = embeds[0]
            else:
                for embed in embeds:
                    if embed.title.startswith(value):
                        break
            await interaction.edit_origin(embed=embed)

    def _init_components(self):
        options = [SelectOption(label='Main Page', value='main_page', emoji='🏠')]

        for _cog in self.bot.cogs:
            cog = self.bot.cogs[_cog]
            if cog.hidden:
                continue

            emoji = cog.emoji
            if isinstance(emoji, int):
                emoji = self.bot.get_emoji(emoji)

            options.append(
                SelectOption(label=_cog, value=_cog, emoji=emoji)
            )

        return [
            Select(
                placeholder='Select module',
                options=options
            )
        ]

    def _init_embeds(self, ctx: SlashContext):
        commands_data = self._get_commands_data()
        embeds = [self._get_main_menu(ctx)]
        for _cog in self.bot.cogs:
            cog = self.bot.cogs[_cog]
            if cog.hidden:
                continue

            embed = Embed(title=f'{_cog} | Asteroid Bot', description='', color=0x2f3136)

            for _base_command in commands_data[_cog]:
                base_command = commands_data[_cog][_base_command]
                for _group in base_command:
                    if _group == 'command_description':
                        continue
                    group = base_command[_group]
                    is_group = group.get('has_subcommand_group')
                    if is_group is None:
                        for _command_name in group:
                            command = group[_command_name]
                            option_line = self.get_options(command)
                            embed.description += f"`/{_base_command} {_group} {_command_name}{option_line}`\n *description:* {command['description']} \n"
                    else:
                        option_line = self.get_options(group)
                        embed.description += f"`/{_base_command} {_group}{option_line}`\n *description:* {group['description']} \n"
            embeds.append(embed)
        return embeds

    def _get_main_menu(self, ctx: SlashContext) -> Embed:
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('HELP_COMMAND', lang)

        embed = Embed(title='Help | Asteroid Bot', color=0x2f3136)
        embed.add_field(
            name=content['INFORMATION_TEXT'],
            value=content['INFORMATION_CONTENT_TEXT'],
            inline=False
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.set_footer(
            text=content['REQUIRED_BY_TEXT'].format(user=ctx.author),
            icon_url=ctx.author.avatar_url
        )

        content = ''
        for _cog in self.bot.cogs:
            cog = self.bot.cogs[_cog]
            if not cog.hidden:
                content += f'**» {_cog}**\n'

        embed.add_field(name='Plugins', value=content)
        return embed

    @staticmethod
    def get_options(command) -> str:
        options = command['options']
        option_line = ''
        if options is None:
            return option_line
        for _option in options:
            option_name = _option['name']
            option_line += f' [{option_name}]' if _option['required'] else f' ({option_name})'
        return option_line

    def _get_commands_data(self) -> dict:
        commands_data = self._get_subcommands_data()
        _commands = self.bot.slash.commands
        for _command in _commands:
            if _command == 'context':
                continue
            command = _commands[_command]
            cog = command.cog.name
            if cog not in commands_data:
                commands_data[cog] = {}
            if _command in commands_data[cog]:
                continue
            commands_data[cog][_command] = {
                'command_description': command.description
            }

        return commands_data

    def _get_subcommands_data(self) -> dict:
        commands_data = {}
        _subcommands = self.bot.slash.subcommands
        for _slash_command in _subcommands:
            command = _subcommands[_slash_command]
            for _subcommand in command:
                subcommand = command[_subcommand]
                if isinstance(subcommand, dict):
                    for _group in subcommand:
                        group = subcommand[_group]
                        self._append_subcommand(commands_data, group)
                else:
                    self._append_subcommand(commands_data, subcommand)
        return commands_data

    @staticmethod
    def _append_subcommand(commands_data, command):
        cog = command.cog.name
        if cog not in commands_data:
            commands_data[cog] = {}
        if command.base not in commands_data[cog]:
            commands_data[cog][command.base] = {}

        has_subcommand_group = command.subcommand_group is not None
        if has_subcommand_group:
            if command.subcommand_group not in commands_data[cog][command.base]:
                commands_data[cog][command.base][command.subcommand_group] = {}
            commands_data[cog][command.base][command.subcommand_group][command.name] = {
                    'description': command.description,
                    'options': command.options
            }
        else:
            commands_data[cog][command.base][command.name] = {
                    'has_subcommand_group': False,
                    'description': command.description,
                    'options': command.options
            }


def setup(bot):
    bot.add_cog(Help(bot))
