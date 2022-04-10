import asyncio
import contextlib
import os
import sys
from datetime import datetime, timedelta, timezone

from discord import Embed, Forbidden
from discord.ext.commands import is_owner
from discord_slash import Button, ButtonStyle, ComponentContext, Select, SelectOption, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand

from utils import AsteroidBot, Cog, DiscordColors


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
        with contextlib.suppress(RuntimeError):
            for count, extension in enumerate(extensions, start=1):
                try:
                    self.bot.reload_extension(extension)
                except Exception as e:
                    content += f"\n`{count}/{extensions_amount}. {extension} `❌"
                    content += f"\n*Ошибка:* `{e}`"
                else:
                    content += f"\n`{count}/{extensions_amount}. {extension} `✅"
        embed = Embed(title="Перезагрузка расширений", description=content, color=0x2F3136)
        await ctx.send(embed=embed)

    @slash_subcommand(base="staff", name="deploy", description="Deploy update from GIT")
    @is_owner()
    async def git_pull_updates(self, ctx: SlashContext):
        await ctx.defer()
        preresult = await self.run_shell("git pull")
        result = "NO DATA" if preresult == "" else "\n".join(preresult)
        content = f"```\n{result}\n```"
        embed = Embed(title="Git Sync", description=content, color=0x2F3136)
        await ctx.send(embed=embed, components=self._get_bot_menu_components())

        self.__update_commits_cache()

    def __update_commits_cache(self):
        today = datetime.now(timezone.utc)
        delta_7 = today - timedelta(days=7)
        self.bot.github_repo_commits = list(
            self.bot.github_repo.get_commits(until=today, since=delta_7)
        )

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
        name="shell",
        description="This command allows use shell. Only for Bot Owner",
    )
    @is_owner()
    async def pip_manage(self, ctx: SlashContext, command: str):
        await ctx.defer()
        response = await self.run_shell(command)
        format_response = "\n".join(response)
        if len(format_response) > 2 << 11:
            format_response = response[-3:]
        content = f"```\n{format_response}\n```"

        embed = Embed(title="PowerShell", description=content, color=DiscordColors.EMBED_COLOR)
        await ctx.send(embed=embed, components=self._get_bot_menu_components())

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

    @Cog.listener()
    async def on_button_click(self, ctx: ComponentContext):
        if ctx.custom_id not in [
            "select_reload_extensions",
            "button_reload_bot",
            "button_sync_commands",
            "button_exit",
        ]:
            return

        if (
            ctx.origin_message_id != ctx.origin_message.interaction.id
            and ctx.author_id != ctx.origin_message.interaction.author_id
        ):
            return

        if ctx.custom_id == "select_reload_extensions":
            extensions = ctx.values
            for extension in extensions:
                self.bot.reload_extension(extension)
            await ctx.send(f'**Reloaded:**\n `{", ".join(extensions)}`')
        elif ctx.custom_id == "button_reload_bot":
            await ctx.defer()
            await ctx.origin_message.disable_components()
            await ctx.send("Reloading...")
            os.execv(sys.executable, ["python3.9"] + sys.argv)
        elif ctx.custom_id == "button_sync_commands":
            await ctx.defer()
            await self.bot.slash.sync_all_commands()
            await ctx.send("Slash Commands were synced!", hidden=True)
        elif ctx.custom_id == "button_exit":
            await ctx.defer(edit_origin=True)
            await ctx.origin_message.disable_components()


def setup(bot):
    bot.add_cog(Settings(bot))
