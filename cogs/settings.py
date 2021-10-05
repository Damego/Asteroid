import os, sys
import discord
from discord.ext import commands
from discord.ext.commands import Cog, MissingPermissions
from discord_slash import SlashContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand
)

from my_utils import AsteroidBot
from my_utils import LANGUAGES_LIST


guild_ids = [
    422989643634442240,
    829333896561819648,
    822119465575383102
]

multiplier = {
    'д': 86400,
    'ч': 3600,
    'м': 60,
    'с': 1,
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1
    }

def is_administrator_or_bot_owner():
    async def predicate(ctx:commands.Context):
        if not ctx.author.guild_permissions.administrator or ctx.author.id != 143773579320754177:
            raise MissingPermissions(['Administrator'])
        return True
    return commands.check(predicate)


class DurationConverter(commands.Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        time_format = argument[-1]

        if amount.isdigit() and time_format in ['д', 'ч', 'м', 'с', 'd', 'h', 'm', 's']:
            return (int(amount), time_format)

        raise commands.BadArgument(message='Wrong time format!')



class Settings(Cog):
    def __init__(self, bot:AsteroidBot) -> None:
        self.bot = bot


    @slash_command(
        name='lang',
        description='Changes bot\'s language on your server [ru, en]',
        guild_ids=guild_ids
    )
    async def set_bot_language(self, ctx: SlashContext, lang: str):
        if lang not in LANGUAGES_LIST:
            return await ctx.send('Wrong language', hidden=True)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id':'configuration'},
            {'$set':{'lang':lang}},
            upsert=True)

        await ctx.send(f'Language was set up to `{lang}`')
        
        

    
    @slash_subcommand(
    base='ext',
    name='load',
    description='Load extension',
    guild_ids=guild_ids
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
        description='Unload extension',
        guild_ids=guild_ids
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
        description='reload extension',
        guild_ids=guild_ids
    )
    @commands.is_owner()
    async def _reload_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.reload_extension(f'cogs.{extension}')
        except Exception as e:
            content = f"""
            Расширение {extension} не загружено!
            Ошибка: {e}
            """
            await ctx.send(content)

    @commands.command()
    async def reload_fucking_slash_commands(self, ctx):
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

        await self.bot.slash.sync_all_commands()

        embed = discord.Embed(title='Перезагрузка расширений', description=content, color=0x2f3136)
        await ctx.send(embed=embed)


    @slash_subcommand(
        base='ext',
        name='reload_all',
        description='Reload all extensions',
        guild_ids=guild_ids
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

        embed = discord.Embed(title='Перезагрузка расширений', description=content, color=0x2f3136)
        await ctx.send(embed=embed)


    @slash_command(
        name='deploy',
        guild_ids=guild_ids,
        description='Deploy update from GIT',
    )
    @commands.is_owner()
    async def git_pull_updates(self, ctx: SlashContext):
        embed = discord.Embed(title='Поиск обновлений...', color=0x2f3136)
        message = await ctx.send(embed=embed)
        os.system('git fetch')
        os.system('git stash')
        embed = discord.Embed(title='Загрузка обновления...', color=0x2f3136)
        await message.edit(embed=embed)
        os.system('git pull')
        embed = discord.Embed(title='Перезагрузка...', color=0x2f3136)
        await message.edit(embed=embed)
        try:
            os.execv(__file__, sys.argv)
        except Exception as e:
            await ctx.send(e)

        extensions = self.bot.extensions
        for extension in extensions:
            try:
                self.bot.reload_extension(extension)
            except Exception:
                pass



def setup(bot):
    bot.add_cog(Settings(bot))