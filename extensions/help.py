import discord
from discord.ext import commands
from discord.ext.commands.errors import BadArgument

from extensions.bot_settings import get_prefix, version



class Help(commands.Cog, description='Помощь'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.hidden = True
        

    @commands.command(description='Показывает помощь по командам', help='[плагин или команда]')
    async def help(self, ctx:commands.Context, arg=None):
        await ctx.message.delete()

        prefix = get_prefix(ctx.guild.id)
        if arg is None:
            embed = self._get_cogs_help(prefix)
        elif arg in self.bot.cogs:
            cog_name = self.bot.cogs[arg].description
            embed = discord.Embed(description=f'```{" " * 15}「📝」{cog_name}```', color=0x2f3136)

            _commands = self.bot.cogs[arg]
            await self.out_commands(_commands, embed, prefix)
        else:
            for command in self.bot.commands:
                if arg == command.name:
                    embed = self._get_command_help(command, prefix)
                    break
            else:
                raise BadArgument

        await ctx.send(embed=embed, delete_after=60)


    async def out_commands(self, cmds, embed, prefix):
        if isinstance(cmds, commands.Group):
            _commands = cmds.commands
        else: _commands = cmds.get_commands()

        for _command in _commands:
            if _command.hidden:
                continue

            embed.add_field(name=f'`{prefix}{_command} {_command.help}`', value=f'*Описание:* {_command.description}', inline=False)

            if isinstance(_command, commands.Group):
                await self.out_commands(_command, embed, prefix)


    def _get_cogs_help(self, prefix):
        embed = discord.Embed(description=f'```{" " * 15}「📝」Команды```', color=0x2f3136)
        embed.add_field(name='Информация о Боте', value=f"""
            **Префикс на сервере:** `{prefix}`
            **Текущая версия Бота:** `{version}`
            """, inline=False)

        for cog in self.bot.cogs:
            if not self.bot.cogs[cog].hidden:
                embed.add_field(name=self.bot.cogs[cog].description, value=f'```{prefix}help {cog}```')

        return embed


    def _get_command_help(self, command:commands.Command, prefix):
        _command = command
        _aliases = ', '.join(_command.aliases) if _command.aliases else 'Нет'
        _usage = _command.usage or 'Всем пользователям'

        embed = discord.Embed(title='Помощь по командам', color=0x2f3136)
        embed.description = f"""
        **Использование:** `{prefix}{_command.name} {_command.help}`
        **Описание:** {_command.description}
        **Псевдонимы:** {_aliases}
        **Доступ к команде:** {_usage}
        """

        return embed



def setup(bot):
    bot.add_cog(Help(bot))