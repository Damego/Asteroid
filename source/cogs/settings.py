import asyncio
import contextlib
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List

from discord import Embed, Forbidden
from discord.ext.commands import is_owner
from discord_slash import Button, ButtonStyle, ComponentContext, Select, SelectOption, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from utils import AsteroidBot, Cog, DiscordColors, consts, load_localization


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
        preresult = await self.start_shell("git pull")
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

    @slash_subcommand(base="staff", name="sync_commands")
    @is_owner()
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
        response = await self.start_shell(command)
        format_response = "\n".join(response) if isinstance(response, list) else response
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

    @Cog.listener(name="on_component")
    async def old_on_component(self, ctx: ComponentContext):
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
            os.execv(sys.executable, ["python"] + sys.argv)
        elif ctx.custom_id == "button_sync_commands":
            await ctx.defer()
            await self.bot.slash.sync_all_commands()
            await ctx.send("Slash Commands were synced!", hidden=True)
        elif ctx.custom_id == "button_exit":
            await ctx.defer(edit_origin=True)
            await ctx.origin_message.disable_components()

    @slash_subcommand(base="staff", name="reload_locales")
    @is_owner()
    async def reload_locales(self, ctx: SlashContext):
        await ctx.defer(hidden=True)
        load_localization()
        await ctx.send("Локализация перезагружена", hidden=True)

    @slash_subcommand(
        base="staff",
        name="control",
    )
    @is_owner()
    async def open_control_menu(self, ctx: SlashContext):
        components = [
            [
                Button(
                    style=ButtonStyle.green,
                    label="Check Bot updates",
                    custom_id="update_bot",
                    emoji="📥",
                ),
                Button(
                    style=ButtonStyle.gray,
                    label="Check discord.py updates",
                    custom_id="update_discord.py",
                    emoji=self.bot.get_emoji(964091772416454676),
                ),
                Button(
                    style=ButtonStyle.gray,
                    label="Check discord-slash updates",
                    custom_id="update_discord-slash",
                    emoji=self.bot.get_emoji(963104705406439425),
                ),
            ],
            [
                Button(
                    style=ButtonStyle.red,
                    label="Reload Bot",
                    custom_id="reload_bot",
                    emoji=self.bot.get_emoji(963104705888804976),
                ),
                Button(
                    style=ButtonStyle.gray,
                    label="Reload all extensions",
                    custom_id="reload_cogs",
                    emoji="🧱",
                ),
                Button(
                    style=ButtonStyle.gray,
                    label="Reload localization",
                    custom_id="reload_locales",
                    emoji="🇺🇸",
                ),
            ],
            [
                Button(
                    style=ButtonStyle.blue,
                    label="Sync commands",
                    custom_id="sync_commands",
                    emoji=self.bot.get_emoji(963104705406439425),
                ),
            ],
            [
                Select(
                    placeholder="Reload extensions",
                    custom_id="reload_extensions",
                    options=[
                        SelectOption(label=extension[5:], value=extension)
                        for extension in self.bot.extensions
                    ],
                    max_values=len(self.bot.extensions),
                ),
            ],
        ]

        embed = Embed(title="Bot Control Menu", color=DiscordColors.EMBED_COLOR)

        await ctx.send(embed=embed, components=components)

    @Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        if ctx.custom_id not in [
            "reload_bot",
            "sync_commands",
            "update_bot",
            "update_discord.py",
            "update_discord-slash",
            "reload_all_extensions",
            "reload_locales",
            "reload_extensions",
        ]:
            return

        if ctx.author_id not in consts.owner_ids:
            return await ctx.send("❌ You are not owner of this bot!", hidden=True)

        await ctx.defer(hidden=True)

        match ctx.custom_id:
            case "reload_bot":
                await ctx.send("Перезагрузка", hidden=True)
                os.execv(sys.executable, ["python"] + sys.argv)
            case "sync_commands":
                try:
                    await self.bot.slash.sync_all_commands()
                except Forbidden:
                    await ctx.send("Невозможно синхронизовать слэш команды", hidden=True)
                else:
                    await ctx.send("Слэш команды были синронизированы", hidden=True)
            case "update_bot":
                result = await self.start_shell("git pull")
                embed = Embed(title="Git Sync", description=result, color=DiscordColors.EMBED_COLOR)
                await ctx.send(embed=embed, hidden=True)
                self.__update_commits_cache()
            case "reload_all_extensions" | "reload_extensions":
                embed = self.__reload_extensions(ctx.values if ctx.values else None)
                await ctx.send(embed=embed, hidden=True)
            case "reload_locales":
                if not_loaded := load_localization():
                    await ctx.send(
                        f"Невозможно перезагрузить локализацию для `{', '.join(not_loaded)}`",
                        hidden=True,
                    )
                else:
                    await ctx.send("Локализация перезагружена", hidden=True)
            case "update_discord.py" | "update_discord-slash":
                to_remove = (
                    "discord.py"
                    if ctx.custom_id == "update_discord_py"
                    else "discord-py-slash-command"
                )
                to_install = (
                    "discord.py"
                    if ctx.custom_id == "update_discord_py"
                    else "discord-py-interactions"
                )
                library = ctx.custom_id.replace("_", " ").capitalize()
                embed_uninstall = Embed(title=library, color=DiscordColors.EMBED_COLOR)
                embed_install = Embed(title=library, color=DiscordColors.EMBED_COLOR)
                embed_uninstall.description = await self.start_shell(
                    f"pip uninstall --yes {to_remove}"
                )
                embed_install.description = await self.start_shell(
                    f"pip install --upgrade git+https://github.com/Damego/{to_install}.git"
                )
                await ctx.send(embeds=[embed_uninstall, embed_install], hidden=True)

    async def start_shell(self, command: str) -> str:
        result = await self.__run_shell(command)
        return f"```\n{''.join(result)}\n```" if result else "NO DATA"

    @staticmethod
    async def __run_shell(command: str):
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

    def __reload_extensions(self, extensions: List[str] = None):
        extensions = extensions or self.bot.extensions
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
        return Embed(
            title="Перезагрузка расширений", description=content, color=DiscordColors.EMBED_COLOR
        )


def setup(bot):
    bot.add_cog(Settings(bot))
