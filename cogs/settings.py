import asyncio
import os
import sys

from discord import Embed
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand
)
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_components import Select, SelectOption, Button, ButtonStyle
from discord_slash_components_bridge import ComponentContext

from my_utils import (
    AsteroidBot,
    get_content,
    bot_owner_or_permissions,
    Cog
)
from my_utils.consts import LANGUAGES_LIST


class Settings(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = '🛠️'
        self.name = 'Settings'

    @slash_subcommand(
        base='set',
        name='lang',
        description='Changes bot\'s language on your server.',
        options=[
            create_option(
                name='language',
                description='Language',
                option_type=3,
                required=True,
                choices=[
                    create_choice(
                        name=language,
                        value=language
                    )
                    for language in LANGUAGES_LIST
                ]
            )
        ]
    )
    @bot_owner_or_permissions(manage_roles=True)
    async def set_bot_language(self, ctx: SlashContext, language: str):
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'configuration'},
            {'$set': {'lang': language}},
            upsert=True)

        await ctx.send(f'Language was set up to `{language}`')

    @slash_subcommand(
        base='set',
        name='color',
        description='Set color for embeds'
    )
    @bot_owner_or_permissions(manage_roles=True)
    async def set_embed_color(self, ctx: SlashContext, color: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('SET_EMBED_COLOR_COMMAND', lang)

        if color.startswith('#') and len(color) == 7:
            color = color.replace('#', '')
        elif len(color) != 6:
            await ctx.send(content['WRONG_COLOR'])
            return
        newcolor = '0x' + color

        collection = self.bot.get_guild_configuration_collection(ctx.guild.id)
        collection.update_one(
            {'_id': 'configuration'},
            {'$set': {'embed_color': newcolor}},
            upsert=True
        )

        embed = Embed(title=content['SUCCESSFULLY_CHANGED'], color=int(newcolor, 16))
        await ctx.send(embed=embed, delete_after=10)

    @slash_subcommand(
        base='set',
        name='status',
        description='Disable all commands in cogs (if implemented)'
    )
    @bot_owner_or_permissions(manage_roles=True)
    async def set_cog_status(self, ctx: SlashContext, cog: str, status: bool):
        await ctx.defer()
        cogs_names = [self.bot.cogs[_cog].name for _cog in self.bot.cogs]
        if cog not in cogs_names:
            return await ctx.send('Cog not found!')

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'cogs_status'},
            {'$set': {
                cog: status
            }
            },
            upsert=True
        )
        await ctx.send('Changed!')

    @slash_subcommand(
        base='ext',
        name='load',
        description='Load extension'
    )
    @commands.is_owner()
    async def _load_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.load_extension(f'cogs.{extension}')
        except Exception as e:
            content = f"""
            Расширение {extension} не загружено!
            Ошибка: {e}
            """
            await ctx.send(content)
        else:
            await ctx.send(f'Плагин {extension} загружен!')

    @slash_subcommand(
        base='ext',
        name='unload',
        description='Unload extension'
    )
    @commands.is_owner()
    async def _unload_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.unload_extension(f'cogs.{extension}')
        except Exception:
            await ctx.send(f'Плагин {extension} не загружен')
        else:
            await ctx.send(f'Плагин {extension} отключен!')

    @slash_subcommand(
        base='ext',
        name='reload',
        description='reload extension'
    )
    @commands.is_owner()
    async def _reload_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.reload_extension(f'cogs.{extension}')
            content = 'Перезагружено!'
        except Exception as e:
            content = f"""
            Расширение {extension} не загружено!
            Ошибка: {e}
            """
        await ctx.send(content)

    @slash_subcommand(
        base='ext',
        name='reload_all',
        description='Reload all extensions'
    )
    @commands.is_owner()
    async def _reload_all_extensions(self, ctx: SlashContext):
        extensions = self.bot.extensions
        extensions_amount = len(extensions)
        content = ''
        try:
            for count, extension in enumerate(extensions, start=1):
                try:
                    self.bot.reload_extension(extension)
                except Exception as e:
                    content += f'\n`{count}/{extensions_amount}. {extension} `❌'
                    content += f'\n*Ошибка:* `{e}`'
                else:
                    content += f'\n`{count}/{extensions_amount}. {extension} `✅'
        except RuntimeError:
            pass

        embed = Embed(title='Перезагрузка расширений', description=content, color=0x2f3136)
        await ctx.send(embed=embed)

    @slash_command(
        name='deploy',
        description='Deploy update from GIT'
    )
    @commands.is_owner()
    async def git_pull_updates(self, ctx: SlashContext):
        components = [
            Select(
                placeholder='Reload extensions',
                custom_id='select_reload_extensions',
                options=[SelectOption(label=extension[5:], value=extension) for extension in self.bot.extensions],
                max_values=len(self.bot.extensions)
            ),
            [
                Button(style=ButtonStyle.blue, label='Reload bot', custom_id='button_reload_bot'),
                Button(style=ButtonStyle.blue, label='Sync commands', custom_id='button_sync_commands'),
                Button(style=ButtonStyle.red, label='Exit', custom_id='button_exit'),
            ]
        ]

        preresult = await self.run_shell('git pull')
        result = 'NO DATA' if preresult == '' else '\n'.join(preresult)
        content = f'```\n{result}\n```'
        embed = Embed(title='Git Sync', description=content, color=0x2f3136)

        message = await ctx.send(embed=embed, components=components)

        while True:
            interaction: ComponentContext = await self.bot.wait_for(
                'component',
                check=lambda inter: inter.message.id == message.id and inter.author_id == ctx.author_id
            )
            if interaction.custom_id == 'select_reload_extensions':
                extensions = interaction.values
                for extension in extensions:
                    self.bot.reload_extension(extension)
                await interaction.send(f'**Reloaded:**\n `{", ".join(extensions)}`')
            elif interaction.custom_id == 'button_reload_bot':
                await interaction.defer(edit_origin=True)
                await interaction.message.disable_components()
                await ctx.channel.send('Reloading...')
                os.execv(sys.executable, ['python3.9'] + sys.argv)
            elif interaction.custom_id == 'button_sync_commands':
                await self.bot.slash.sync_all_commands()
                await ctx.send('Slash Commands were synced!', hidden=True)
            elif interaction.custom_id == 'button_exit':
                await interaction.defer(edit_origin=True)
                await interaction.message.disable_components()
                return

    @staticmethod
    async def run_shell(command: str):
        process = await asyncio.create_subprocess_shell(
            command,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        try:
            stdout = stdout.decode(encoding='UTF-8')
        except UnicodeDecodeError:
            stdout = ''
        try:
            stderr = stderr.decode(encoding='UTF-8')
        except UnicodeDecodeError:
            stderr = ''
        return stdout, stderr

    @slash_command(
        name='sync_commands',
        guild_ids=[422989643634442240]
    )
    async def _sync_commands(self, ctx: SlashContext):
        await self.bot.slash.sync_all_commands()
        await ctx.send('Синхронизировано!')


def setup(bot):
    bot.add_cog(Settings(bot))
