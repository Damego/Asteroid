import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

from discord import Embed, Forbidden
from discord.ext.commands import is_owner
from discord_slash import (
    SlashContext,
    Select,
    SelectOption,
    Button,
    ButtonStyle,
    ComponentContext,
)
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from utils import AsteroidBot, Cog


class Settings(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = "🛠️"
        self.name = "Settings"
        self.hidden = True

    @slash_subcommand(
        base="staff", subcommand_group="ext", name="load", description="Load extension"
    )
    @is_owner()
    async def _load_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.load_extension(f"cogs.{extension}")
        except Exception as e:
            content = f"""
            Расширение {extension} не загружено!
            Ошибка: {e}
            """
            await ctx.send(content)
        else:
            await ctx.send(f"Плагин {extension} загружен!")

    @slash_subcommand(
        base="staff",
        subcommand_group="ext",
        name="unload",
        description="Unload extension",
    )
    @is_owner()
    async def _unload_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.unload_extension(f"cogs.{extension}")
        except Exception:
            await ctx.send(f"Плагин {extension} не загружен")
        else:
            await ctx.send(f"Плагин {extension} отключен!")

    @slash_subcommand(
        base="staff",
        subcommand_group="ext",
        name="reload",
        description="reload extension",
    )
    @is_owner()
    async def _reload_extension(self, ctx: SlashContext, extension):
        try:
            self.bot.reload_extension(f"cogs.{extension}")
            content = "Перезагружено!"
        except Exception as e:
            content = f"""
            Расширение {extension} не загружено!
            Ошибка: {e}
            """
        await ctx.send(content)

    @slash_subcommand(
        base="staff",
        subcommand_group="ext",
        name="reload_all",
        description="Reload all extensions",
    )
    @is_owner()
    async def _reload_all_extensions(self, ctx: SlashContext):
        extensions = self.bot.extensions
        extensions_amount = len(extensions)
        content = ""
        try:
            for count, extension in enumerate(extensions, start=1):
                try:
                    self.bot.reload_extension(extension)
                except Exception as e:
                    content += f"\n`{count}/{extensions_amount}. {extension} `❌"
                    content += f"\n*Ошибка:* `{e}`"
                else:
                    content += f"\n`{count}/{extensions_amount}. {extension} `✅"
        except RuntimeError:
            pass

        embed = Embed(
            title="Перезагрузка расширений", description=content, color=0x2F3136
        )
        await ctx.send(embed=embed)

    @slash_subcommand(base="staff", name="deploy", description="Deploy update from GIT")
    @is_owner()
    async def git_pull_updates(self, ctx: SlashContext):
        await ctx.defer()
        preresult = await self.run_shell("git pull")
        result = "NO DATA" if preresult == "" else "\n".join(preresult)
        content = f"```\n{result}\n```"
        embed = Embed(title="Git Sync", description=content, color=0x2F3136)

        self.__update_commits_cache()

        message = await ctx.send(
            embed=embed, components=self._get_bot_menu_components()
        )
        await self._run_bot_menu(ctx, message)

    def __update_commits_cache(self):
        today = datetime.now(timezone.utc)
        delta_7 = today - timedelta(days=7)
        self.bot.github_repo_commits = list(self.bot.github_repo.get_commits(until=today, since=delta_7))

    @staticmethod
    async def run_shell(command: str):
        process = await asyncio.create_subprocess_shell(
            command, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        try:
            stdout = stdout.decode(encoding="UTF-8")
        except UnicodeDecodeError:
            stdout = ""
        try:
            stderr = stderr.decode(encoding="UTF-8")
        except UnicodeDecodeError:
            stderr = ""
        return stdout, stderr

    @slash_subcommand(base="staff", name="sync_commands")
    async def sync_commands(self, ctx: SlashContext):
        await ctx.defer()
        try:
            await self.bot.slash.sync_all_commands()
        except Forbidden:
            await ctx.send("Cannot sync slash commands!")
        else:
            await ctx.send("Slash commands were synced!")

    @slash_subcommand(
        base="staff",
        name="pip",
        description="This command allows use pip to manage python libraries",
    )
    @is_owner()
    async def pip_manage(self, ctx: SlashContext, command: str):
        await ctx.defer()
        response = await self.run_shell(f"python3.9 -m pip {command}")
        format_response = "\n".join(response)
        if len(format_response) > 2 << 11:
            format_response = response[-3:]
        content = f"```\n{format_response}\n```"

        embed = Embed(title="PIP", description=content, color=0x2F3136)
        message = await ctx.send(
            embed=embed, components=self._get_bot_menu_components()
        )
        await self._run_bot_menu(ctx, message)

    def _get_bot_menu_components(self):
        return [
            Select(
                placeholder="Reload extensions",
                custom_id="select_reload_extensions",
                options=[
                    SelectOption(label=extension[5:], value=extension)
                    for extension in self.bot.extensions
                ],
                max_values=len(self.bot.extensions),
            ),
            [
                Button(
                    style=ButtonStyle.blue,
                    label="Reload bot",
                    custom_id="button_reload_bot",
                ),
                Button(
                    style=ButtonStyle.blue,
                    label="Sync commands",
                    custom_id="button_sync_commands",
                ),
                Button(style=ButtonStyle.red, label="Exit", custom_id="button_exit"),
            ],
        ]

    async def _run_bot_menu(self, ctx: SlashContext, message):
        while True:
            button_ctx: ComponentContext = await self.bot.wait_for(
                "component",
                check=lambda inter: inter.origin_message.id == message.id
                and inter.author_id == ctx.author_id,
            )
            if button_ctx.custom_id == "select_reload_extensions":
                extensions = button_ctx.values
                for extension in extensions:
                    self.bot.reload_extension(extension)
                await button_ctx.send(f'**Reloaded:**\n `{", ".join(extensions)}`')
            elif button_ctx.custom_id == "button_reload_bot":
                await button_ctx.defer(edit_origin=True)
                await button_ctx.origin_message.disable_components()
                await ctx.channel.send("Reloading...")
                os.execv(sys.executable, ["python3.9"] + sys.argv)
            elif button_ctx.custom_id == "button_sync_commands":
                await button_ctx.defer()
                await self.bot.slash.sync_all_commands()
                await ctx.send("Slash Commands were synced!", hidden=True)
            elif button_ctx.custom_id == "button_exit":
                await button_ctx.defer(edit_origin=True)
                await button_ctx.origin_message.disable_components()
                return


def setup(bot):
    bot.add_cog(Settings(bot))
