import contextlib
from datetime import datetime
from traceback import format_exception

from discord import Embed, Forbidden, Guild, TextChannel
from discord.ext.commands import (
    BadArgument,
    BotMissingPermissions,
    CheckFailure,
    MissingPermissions,
    NotOwner,
)
from discord_slash import SlashContext
from genshin.errors import AccountNotFound, DataNotPublic
from utils import (
    AsteroidBot,
    Cog,
    DiscordColors,
    SystemChannels,
    errors,
    get_content,
    transform_permission,
)


class Listeners(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = True

        self.slash_use_channel: TextChannel = None

    # EVENTS
    @Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(SystemChannels.BOT_UPTIME_CHANNEL)
        if channel is None:
            channel = await self.bot.fetch_channel(SystemChannels.BOT_UPTIME_CHANNEL)
        await channel.send(f"{self.bot.user} успешно загружен!")

        print(f"{self.bot.user} загружен!")

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        await self.bot.mongo.add_guild(guild.id)

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        await self.bot.mongo.delete_guild(guild.id)

    @Cog.listener()
    async def on_slash_command(self, ctx: SlashContext):
        if self.bot.is_debug_mode:
            return

        if self.slash_use_channel is None:
            self.slash_use_channel = self.bot.get_channel(SystemChannels.COMMANDS_USING_CHANNEL)

        embed = Embed(
            title=self.bot.get_transformed_command_name(ctx),
            color=DiscordColors.EMBED_COLOR,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(
            text=f"{ctx.author.name} | {ctx.author_id}", icon_url=ctx.author.avatar_url
        )
        if ctx.kwargs:
            options = "\n".join([f"{option}: {value}" for option, value in ctx.kwargs.items()])
            embed.add_field(name="Options", value=options)
        if ctx.guild:
            embed.add_field(
                name="Guild Information",
                value=f"Name: {ctx.guild.name}\nID: {ctx.guild_id}",
            )

        await self.slash_use_channel.send(embed=embed)

    @Cog.listener(name="on_slash_command_error")
    async def on_slash_command_error(self, ctx: SlashContext, error):
        embed = Embed(color=DiscordColors.RED)
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id) if ctx.guild is not None else "en-US"
        content = get_content("ERRORS_DESCRIPTIONS", lang)
        desc = self.get_error_description(error, content)

        if desc is not None:
            embed.description = desc
            with contextlib.suppress(Forbidden):
                return await ctx.send(embed=embed)

        match error:
            case BotMissingPermissions():
                missing_perms = [transform_permission(perm) for perm in error.missing_perms]
                desc = f'{content["BOT_DONT_HAVE_PERMS"]} `{", ".join(missing_perms)}`'
            case MissingPermissions():
                missing_perms = [transform_permission(perm) for perm in error.missing_perms]
                desc = f'{content["DONT_HAVE_PERMS"]} `{", ".join(missing_perms)}`'
            case CheckFailure():
                desc = content["CHECK_FAILURE"]
            case _:
                if self.bot.is_debug_mode:
                    raise error

                desc = content["OTHER_ERRORS_DESCRIPTION"].format(error=error)
                embed.title = content["OTHER_ERRORS_TITLE"]

                error_traceback = "".join(format_exception(type(error), error, error.__traceback__))
                error_embed = self.get_error_embed(ctx, error, error_traceback)
                await self.send_error(error_embed)

        embed.description = desc
        with contextlib.suppress(Forbidden):
            await ctx.send(embed=embed)

    @staticmethod
    def get_error_description(error, content: dict) -> str:
        exceptions = {
            errors.CogDisabledOnGuild: content["COG_DISABLED"],
            errors.CommandDisabled: content["COMMAND_DISABLED"],
            errors.NoData: content["NO_DATA_FOUND"],
            errors.TagNotFound: content["TAG_NOT_FOUND"],
            errors.ForbiddenTag: content["FORBIDDEN_TAG"],
            errors.NotTagOwner: content["NOT_TAG_OWNER"],
            errors.UIDNotBinded: content["UID_NOT_BINDED"],
            AccountNotFound: content["GI_ACCOUNT_NOT_FOUND"],
            DataNotPublic: content["GI_DATA_NOT_PUBLIC"],
            errors.BotNotConnectedToVoice: content["BOT_NOT_CONNECTED"],
            errors.NotConnectedToVoice: content["NOT_CONNECTED_TO_VOICE_TEXT"],
            errors.NotPlaying: content["NOT_PLAYING"],
            errors.NotGuild: content["GUILD_ONLY"],
            errors.PrivateVoiceNotSetup: content["PRIVATE_VOICE_NOT_SETUP"],
            errors.DontHavePrivateRoom: content["DONT_HAVE_PRIVATE_ROOM"],
            errors.MessageWithoutAutoRole: content["MESSAGE_WITHOUT_AUTOROLE"],
            errors.AutoRoleNotFound: content["AUTOROLE_NOT_FOUND"],
            errors.OptionsOverKill: content["OPTIONS_OVERKILL"],
            errors.OptionNotFound: content["OPTION_NOT_FOUND"],
            errors.OptionLessThanOne: content["OPTIONS_LESS_THAN_1"],
            errors.NotSavedAutoRoles: content["NOT_SAVED_AUTOROLES"],
            errors.NotDropDown: content["NOT_DROPDOWN"],
            errors.NotButton: content["NOT_BUTTON"],
            errors.LabelOrEmojiRequired: content["AT_LEAST_LABEL_OR_EMOJI"],
            errors.ButtonsOverKill: content["LIMIT_25_BUTTONS"],
            NotOwner: content["NOT_BOT_OWNER"],
            BadArgument: content["BAD_ARGUMENT"],
            Forbidden: content["FORBIDDEN"],
        }
        return exceptions.get(type(error))

    async def send_error(self, embed: Embed):
        channel = self.bot.get_channel(SystemChannels.ERRORS_CHANNEL)
        if channel is None:
            channel = await self.bot.fetch_channel(SystemChannels.ERRORS_CHANNEL)
        try:
            await channel.send(embed=embed)
        except Forbidden:
            embed.description = "Checks logs"
            await channel.send(embed=embed)

    def get_error_embed(self, ctx: SlashContext, error: Exception, traceback: str) -> Embed:
        embed = Embed(
            title="Unexpected error",
            description=f"``` {traceback} ```",
            timestamp=datetime.utcnow(),
            color=0xED4245,
        )
        embed.add_field(
            name="Command Name", value=f"`/{self.bot.get_transformed_command_name(ctx)}`"
        )
        if ctx.guild is not None:
            embed.add_field(name="Guild", value=f"Name: `{ctx.guild.name}`\n ID:`{ctx.guild_id}`")
            embed.add_field(
                name="Channel",
                value=f"Name: `{ctx.channel.name}`\n ID:`{ctx.channel_id}`",
            )
        embed.add_field(name="User", value=f"Name: `{ctx.author.name}`\n ID:`{ctx.author_id}`")
        embed.add_field(name="Short Description", value=f"`{error}`")

        return embed


def setup(bot):
    bot.add_cog(Listeners(bot))
