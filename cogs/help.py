from asyncio import TimeoutError
import datetime

from discord import Embed
from discord_slash import SlashContext, ComponentContext, Select, SelectOption
from discord_slash.cog_ext import cog_slash as slash_command

from my_utils import AsteroidBot, get_content, Cog


class Help(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = True
        self.name = "Help"
        self.commands_cache: dict = None

    @slash_command(name="help", description="Help and bot commands")
    async def help_command(self, ctx: SlashContext):
        await ctx.defer()

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("HELP_COMMAND", lang)

        components = self._init_components(ctx, content)
        embeds = self._init_embeds(ctx, content, lang)
        message = await ctx.send(embed=embeds[0], components=components)

        while True:
            try:
                button_ctx: ComponentContext = await self.bot.wait_for(
                    "select_option",
                    check=lambda _ctx: _ctx.author_id == ctx.author_id
                    and _ctx.origin_message.id == message.id,
                    timeout=60,
                )
            except TimeoutError:
                return await message.edit(components=[])

            value = button_ctx.values[0]

            if value == "main_page":
                embed = embeds[0]
            else:
                for embed in embeds:
                    if embed.title.startswith(value):
                        break

            for option in components[0][0].options:
                option.default = False
                if option.value == value:
                    option.default = True

            await button_ctx.edit_origin(embed=embed, components=components)

    @staticmethod
    def _cog_is_private(ctx: SlashContext, cog: Cog):
        return cog.private_guild_id and ctx.guild_id not in cog.private_guild_id

    def _init_components(self, ctx: SlashContext, content: dict):
        options_translation = content["PLUGINS"]
        options = [SelectOption(label=options_translation["MAIN_PAGE"], value="main_page", emoji="🏠", default=True)]
        
        for cog_name, cog in self.bot.cogs.items():
            if cog.hidden:
                continue
            if self._cog_is_private(ctx, cog):
                continue

            emoji = cog.emoji
            if isinstance(emoji, int):
                emoji = self.bot.get_emoji(emoji)

            options.append(SelectOption(label=options_translation[cog_name.upper()], value=cog_name, emoji=emoji))

        return [Select(placeholder=content["SELECT_MODULE_TEXT"], options=options)]

    def _init_embeds(self, ctx: SlashContext, content: dict, guild_language: str):
        translated_commands = None
        if guild_language != "English":
            translated_commands = get_content("TRANSLATED_COMMANDS", guild_language)
        commands_data = self._get_commands_data()
        embeds = [self._get_main_menu(ctx, content)]

        for cog_name, cog in self.bot.cogs.items():
            if cog.hidden:
                continue
            if self._cog_is_private(ctx, cog):
                continue

            embed = Embed(
                title=f"{cog_name} | Asteroid Bot",
                description="",
                timestamp=datetime.datetime.utcnow(),
                color=0x2F3136,
            )
            embed.set_footer(
                text=content["REQUIRED_BY_TEXT"].format(user=ctx.author),
                icon_url=ctx.author.avatar_url,
            )
            embed.set_thumbnail(url=ctx.bot.user.avatar_url)

            if cog not in commands_data:
                continue

            cog_commands = commands_data[cog]

            for base_command, base_command_data in cog_commands.items():
                if isinstance(base_command_data, dict):
                    for group_command, group_command_data in base_command_data.items():
                        if isinstance(group_command_data, dict):
                            for command_name, command_data in group_command_data.items():
                                options = self.get_options(command_data)
                                command_description = (
                                    translated_commands.get(
                                    f"{base_command}_{group_command}_{command_name}".upper(),
                                    command_data.description,
                                    )
                                    if translated_commands
                                    else command_data.description
                                )
                                embed.description += (
                                    f"`/{base_command} {group_command} {command_name}{options}`\n "
                                    f"*{content['DESCRIPTION_TEXT']}* {command_description} \n"
                                )
                        else:
                            options = self.get_options(group_command_data)
                            command_description = (
                                translated_commands.get(
                                f"{base_command}_{group_command}".upper(),
                                group_command_data.description,
                                )
                                if translated_commands
                                else group_command_data.description
                            )
                            embed.description += (
                                f"`/{base_command} {group_command}{options}`\n "
                                f"*{content['DESCRIPTION_TEXT']}* {command_description} \n"
                            )
                else:
                    options = self.get_options(base_command_data)
                    command_description = (
                        translated_commands.get(
                        f"{base_command}".upper(),
                        base_command_data.description,
                        )
                        if translated_commands
                        else base_command_data.description
                    )
                    embed.description += (
                        f"`/{base_command}{options}`\n "
                        f"*{content['DESCRIPTION_TEXT']}* {command_description} \n"
                    )
            embeds.append(embed)

        return embeds

    def _get_main_menu(self, ctx: SlashContext, content: dict) -> Embed:
        embed = Embed(
            title="Help | Asteroid Bot",
            timestamp=datetime.datetime.utcnow(),
            color=0x2F3136,
        )
        embed.add_field(
            name=content["INFORMATION_TEXT"],
            value=content["INFORMATION_CONTENT_TEXT"],
            inline=False,
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.set_footer(
            text=content["REQUIRED_BY_TEXT"].format(user=ctx.author),
            icon_url=ctx.author.avatar_url,
        )

        options_translation = content["PLUGINS"]
        cogs = ""
        for cog_name, cog in self.bot.cogs.items():
            if cog.hidden:
                continue
            if cog.private_guild_id and ctx.guild_id not in cog.private_guild_id:
                continue
            cogs += f"**» {options_translation[cog_name.upper()]}**\n"

        embed.add_field(name=content["PLUGINS_TEXT"], value=cogs)
        return embed

    @staticmethod
    def get_options(command) -> str:
        options = command.options
        option_line = ""
        if options is None:
            return option_line
        for _option in options:
            option_name = _option["name"]
            option_line += (
                f" [{option_name}]" if _option["required"] else f" ({option_name})"
            )
        return option_line

    def _get_commands_data(self):
        if self.commands_cache is not None:
            return self.commands_cache

        commands_data = self._get_subcommands_data()
        commands = self.bot.slash.commands
        for command_name, command_data in commands.items():
            if command_name in ["context", "Profile"] or not command_data:
                continue
            if command_data.cog not in commands_data:
                commands_data[command_data.cog] = {}
            if command_name in commands_data[command_data.cog]:
                continue
            commands_data[command_data.cog][command_name] = command_data

        self.commands_cache = commands_data
        return commands_data

    def _get_subcommands_data(self):
        commands_data = {}
        subcommands = self.bot.slash.subcommands
        for base_name, group in subcommands.items():
            if base_name == "context":
                continue
            for group_name, group_data in group.items():
                if isinstance(group_data, dict):
                    for command_name, model in group_data.items():
                        if model.cog not in commands_data:
                            commands_data[model.cog] = {}
                        if base_name not in commands_data[model.cog]:
                            commands_data[model.cog][base_name] = {}
                        if group_name not in commands_data[model.cog][base_name]:
                            commands_data[model.cog][base_name][group_name] = {}
                        commands_data[model.cog][base_name][group_name][command_name] = model
                else:
                    if group_data.cog not in commands_data:
                        commands_data[group_data.cog] = {}
                    if base_name not in commands_data[group_data.cog]:
                        commands_data[group_data.cog][base_name] = {}
                    commands_data[group_data.cog][base_name][group_name] = group_data
        return commands_data

def setup(bot):
    bot.add_cog(Help(bot))
