import asyncio
import discord
from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from discord_components import Interaction, Select, SelectOption

from .bot_settings import version
from mongobot import MongoComponentsBot



class Help(commands.Cog, description='Help'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.bot.remove_command('help')
        self.hidden = True
        

    @commands.command(description='Show this message', help='(plugin or command)')
    async def help(self, ctx:commands.Context, arg=None):
        prefix = ctx.prefix
        components = []

        if arg is None:
            embeds = [self._get_main_menu(prefix)]
            select_options = [SelectOption(label='Main page', value='main_page', emoji='🌐')]

            for _cog in self.bot.cogs:
                cog = self.bot.cogs[_cog]
                if cog.hidden:
                    continue
                embed = discord.Embed(title=f'{_cog} | {cog.description}', color=0x2f3136)
                embeds.append(self.out_commands(cog, embed, prefix))

                emoji = cog.emoji
                if isinstance(emoji, int):
                    emoji = self.bot.get_emoji(emoji)

                select_options.append(
                    SelectOption(label=f'{_cog} | {cog.description}', value=_cog, emoji=emoji)
                )

            components = [
                Select(
                    placeholder='Choose category',
                    options=select_options
                )
            ]

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
                try:
                    interaction:Interaction = await self.bot.wait_for(
                        'select_option',
                        timeout=120,
                        check=lambda i: i.user.id == ctx.author.id)
                except asyncio.TimeoutError:
                    return await message.edit(components=[])
                except Exception:
                    continue

                value = interaction.values[0]
                if value == 'main_page':
                    try:
                        await interaction.respond(type=7, embed=embeds[0])
                    except Exception:
                        pass
                    finally:
                        continue
                
                for embed in embeds:
                    if embed.title.startswith(value):
                        try:
                            await interaction.respond(type=7, embed=embed)
                        except Exception:
                            continue
                        finally:
                            break
        else:
            await ctx.send(embed=embed, delete_after=60)


    def out_commands(self, cmds, embed, prefix):
        if isinstance(cmds, commands.Group):
            _commands = cmds.commands
        else: _commands = cmds.get_commands()

        for _command in _commands:
            if _command.hidden:
                continue

            embed.add_field(name=f'`{prefix}{_command} {_command.help}`', value=f'*Description:* {_command.description}', inline=False)

            if isinstance(_command, commands.Group):
                self.out_commands(_command, embed, prefix)

        return embed


    def _get_main_menu(self, prefix):
        embed = discord.Embed(title='Commands Asteroid Bot', color=0x2f3136)
        embed.add_field(name='Information', value=f"""
            *Hint:* `{prefix}help [plugin or command]` for more information.
            """, inline=False)

        content = ''
        for _cog in self.bot.cogs:
            cog = self.bot.cogs[_cog]
            if not cog.hidden:
                content += f'**» {_cog}** | {cog.description}\n'

        embed.add_field(name='Plugins', value=content)
        return embed


    def _get_command_help(self, command:commands.Command, prefix):
        _command = command
        _aliases = ', '.join(_command.aliases) if _command.aliases else 'Нет'
        _usage = _command.usage or 'Everyone'

        embed:discord.Embed = discord.Embed(title=f'Command: {_command.name}', color=0x2f3136)
        embed.description = f"""
        **Usage:** `{prefix}{_command.name} {_command.help}`
        **Description:** {_command.description}
        **Aliases:** {_aliases}
        **Access to the command:** {_usage}
        """

        return embed



def setup(bot):
    bot.add_cog(Help(bot))