import discord
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from discord_components import Interaction

from .bot_settings import (
    PaginatorStyle,
    PaginatorCheckButtonID,
    get_interaction,
    version
    )
from mongobot import MongoComponentsBot



class Help(commands.Cog, description='Помощь'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.bot.remove_command('help')
        self.hidden = True
        

    @commands.command(description='Показывает помощь по командам', help='[плагин или команда]')
    async def help(self, ctx:commands.Context, arg=None):
        prefix = self.bot.get_guild_prefix(ctx.guild.id)
        components = []

        if arg is None:
            pages = 1
            embeds = [self._get_main_menu(prefix)]

            for _cog in self.bot.cogs:
                cog = self.bot.cogs[_cog]
                if cog.hidden:
                    continue
                embed = discord.Embed(title=f'{_cog} | {cog.description}', color=0x2f3136)
                embeds.append(self.out_commands(cog, embed, prefix))
                pages += 1

            page = 1
            components = PaginatorStyle.style1(pages)

        elif arg in self.bot.cogs:
            cog_name = arg
            cog_name_ru = self.bot.cogs[arg].description
            embed = discord.Embed(title=f'{cog_name} | {cog_name_ru}', color=0x2f3136)

            _commands = self.bot.cogs[arg]
            self.out_commands(_commands, embed, prefix)
        else:
            for _command in self.bot.commands:
                if arg == _command.name or arg in _command.aliases:
                    embed = self._get_command_help(_command, prefix)
                    if isinstance(_command, commands.Group):
                        self.out_commands(_command, embed, prefix)
                    break
            else:
                raise BadArgument

        if components:
            message = await ctx.send(embed=embeds[0], components=components)

            while True:
                interaction:Interaction = await get_interaction(self.bot, ctx, message)
                if interaction is None:
                    return

                button_id = interaction.component.id
                paginator = PaginatorCheckButtonID(components, pages)
                page = paginator._style1(button_id, page)

                try:
                    await interaction.respond(type=7, embed=embeds[page-1], components=components)
                except Exception:
                    continue
        else:
            await ctx.send(embed=embed, delete_after=60)


    def out_commands(self, cmds, embed, prefix):
        if isinstance(cmds, commands.Group):
            _commands = cmds.commands
        else: _commands = cmds.get_commands()

        for _command in _commands:
            if _command.hidden:
                continue

            embed.add_field(name=f'`{prefix}{_command} {_command.help}`', value=f'*Описание:* {_command.description}', inline=False)

            if isinstance(_command, commands.Group):
                self.out_commands(_command, embed, prefix)

        return embed


    def _get_main_menu(self, prefix):
        embed = discord.Embed(title='Команды Asteroid Bot', color=0x2f3136)
        embed.add_field(name='Информация', value=f"""
            **Текущая версия Бота:** `{version}`
            **Префикс на сервере:** `{prefix}`
            *Подсказка:* `{prefix}help [Плагин или команда]` для показа подробностей. 
            """, inline=False)

        content = ''
        for _cog in self.bot.cogs:
            cog = self.bot.cogs[_cog]
            if not cog.hidden:
                content += f'**» {_cog}** | {cog.description}\n'

        embed.add_field(name='Плагины', value=content)
        return embed


    def _get_command_help(self, command:commands.Command, prefix):
        _command = command
        _aliases = ', '.join(_command.aliases) if _command.aliases else 'Нет'
        _usage = _command.usage or 'Всем пользователям'

        embed:discord.Embed = discord.Embed(title=f'Команда: {_command.name}', color=0x2f3136)
        embed.description = f"""
        **Использование:** `{prefix}{_command.name} {_command.help}`
        **Описание:** {_command.description}
        **Псевдонимы:** {_aliases}
        **Доступ к команде:** {_usage}
        """

        return embed



def setup(bot):
    bot.add_cog(Help(bot))