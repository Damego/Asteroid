from typing import Tuple, Union

from discord import Embed, Member, PermissionOverwrite, TextChannel, VoiceChannel, VoiceState
from discord.ext.commands import bot_has_guild_permissions
from discord_slash import (
    Button,
    ComponentContext,
    Modal,
    ModalContext,
    Select,
    SelectOption,
    SlashCommandOptionType,
    SlashContext,
    TextInput,
    TextInputStyle,
)
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option
from utils import (
    AsteroidBot,
    Cog,
    DiscordColors,
    DontHavePrivateRoom,
    GuildData,
    GuildPrivateVoice,
    bot_owner_or_permissions,
    cog_is_enabled,
    get_content,
    is_enabled,
)


class PrivateRooms(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.emoji = "🔊"
        self.name = "PrivateRooms"

    async def __check(
        self, ctx: SlashContext, *, return_guild_data: bool = False
    ) -> Union[Tuple[VoiceChannel, dict], Tuple[VoiceChannel, dict, GuildData]]:
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        active_channels = guild_data.private_voice.active_channels
        content = get_content("PRIVATE_VOICE", guild_data.configuration.language)
        if str(ctx.author_id) not in active_channels:
            raise DontHavePrivateRoom
        voice_channel: VoiceChannel = ctx.guild.get_channel(active_channels[str(ctx.author_id)])

        if return_guild_data:
            return voice_channel, content, guild_data
        return voice_channel, content

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="close",
        description="Closes your room",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_close(self, ctx: SlashContext):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send(content["ROOM_CLOSED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="open",
        description="Opens your room",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_open(self, ctx: SlashContext):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.set_permissions(ctx.guild.default_role, connect=True)
        await ctx.send(content["ROOM_OPENED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="hide",
        description="Hides your room",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_hide(self, ctx: SlashContext):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(content["ROOM_HIDED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="unhide",
        description="Unhides your room",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_unhide(self, ctx: SlashContext):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send(content["ROOM_UNHIDED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="change_name",
        description="Change room name",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_change__name(self, ctx: SlashContext, name: str):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.edit(name=name)
        await ctx.send(content["ROOM_NAME_WAS_SETUP"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="ban",
        description="Bans member to room",
    )
    @is_enabled()
    @bot_has_guild_permissions(move_members=True, manage_channels=True)
    async def private__rooms_control_ban(self, ctx: SlashContext, member: Member):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.set_permissions(member, connect=False)
        if member.voice and member.voice.channel.id == voice_channel.id:
            await member.move_to(None)
        await ctx.send(content["MEMBER_WAS_BANNED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="unban",
        description="Unbans member from room",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_unban(self, ctx: SlashContext, member: Member):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.set_permissions(member, connect=True)
        await ctx.send(content["MEMBER_WAS_UNBANNED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="kick",
        description="Kicks a member from room",
    )
    @is_enabled()
    @bot_has_guild_permissions(move_members=True, manage_channels=True)
    async def private__rooms_control_kick(self, ctx: SlashContext, member: Member):
        voice_channel, content = await self.__check(ctx)

        if member.voice and member.voice.channel.id == voice_channel.id:
            await member.move_to(None)
        await ctx.send(content["MEMBER_WAS_KICKED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="transfer_ownership",
        description="Transfer room ownership",
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_transfer__ownership(self, ctx: SlashContext, member: Member):
        voice_channel, content, guild_data = await self.__check(ctx, return_guild_data=True)

        await guild_data.private_voice.set_private_voice_channel(member.id, voice_channel.id)
        await voice_channel.set_permissions(
            member, manage_channels=True, connect=True, move_members=True
        )
        await voice_channel.set_permissions(
            ctx.author, manage_channels=False, connect=False, move_members=False
        )
        await ctx.send(content["OWNERSHIP_TRANSFERED"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        subcommand_group="control",
        name="set_limit",
        description="Sets room limit",
        options=[
            create_option(
                name="limit",
                description="The limit of members in your room",
                option_type=SlashCommandOptionType.INTEGER,
                min_value=1,
                max_value=99,
            )
        ],
    )
    @is_enabled()
    @bot_has_guild_permissions(manage_channels=True)
    async def private__rooms_control_set__limit(self, ctx: SlashContext, limit: int):
        voice_channel, content = await self.__check(ctx)

        await voice_channel.edit(user_limit=limit)
        await ctx.send(content["LIMIT_WAS_SETUP"], hidden=True)

    @slash_subcommand(
        base="private_rooms",
        name="create_menu",
        description="Creates a control menu",
    )
    @is_enabled()
    @bot_has_guild_permissions(move_members=True, manage_channels=True)
    @bot_owner_or_permissions(manage_guild=True)
    async def private__rooms_create__menu(self, ctx: SlashContext):
        await ctx.defer(hidden=True)

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("PRIVATE_VOICE", guild_data.configuration.language)
        components = [
            [
                Button(emoji=self.bot.get_emoji(959124362840113182), custom_id="voice_close"),
                Button(emoji=self.bot.get_emoji(959124362890461254), custom_id="voice_open"),
                Button(emoji=self.bot.get_emoji(959124362890461325), custom_id="voice_hide"),
                Button(emoji=self.bot.get_emoji(959124362890473582), custom_id="voice_unhide"),
                Button(
                    emoji=self.bot.get_emoji(959124362798174319), custom_id="voice_change_room_name"
                ),
            ],
            [
                Button(emoji=self.bot.get_emoji(959124362882068550), custom_id="voice_ban"),
                Button(emoji=self.bot.get_emoji(959124362835931236), custom_id="voice_unban"),
                Button(emoji=self.bot.get_emoji(959124362974343169), custom_id="voice_kick"),
                Button(emoji=self.bot.get_emoji(959124362823340052), custom_id="voice_transfer"),
                Button(
                    emoji=self.bot.get_emoji(959124362835927080), custom_id="voice_set_room_limit"
                ),
            ],
        ]

        category = await ctx.guild.create_category(content["PRIVATE_ROOMS"])
        voice_channel = await category.create_voice_channel(content["CREATE_ROOM"])
        overwrites = {
            ctx.guild.default_role: PermissionOverwrite(
                send_messages=False, use_slash_commands=False
            )
        }
        text_channel: TextChannel = await category.create_text_channel(
            content["ROOM_CONTROL"], overwrites=overwrites
        )
        await guild_data.create_private_voice(text_channel.id, voice_channel.id)
        embed = Embed(
            title=content["ROOM_CONTROL_TITLE"],
            description="".join(content["ROOM_CONTROL_DESCRIPTION"]),
            color=DiscordColors.EMBED_COLOR,
        )

        await text_channel.send(embed=embed, components=components)

        await ctx.send(content["SUCCESSFULLY_CREATED"])

    @Cog.listener()
    @cog_is_enabled()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        guild_data = await self.bot.get_guild_data(member.guild.id)
        private_voice = guild_data.private_voice
        voice_channel_id = private_voice.voice_channel_id
        if after.channel and after.channel.id == voice_channel_id:
            if before.channel:
                await self._check_channel(member, before, private_voice)

            # Creating a private voice channel
            overwrites = {
                member.guild.default_role: PermissionOverwrite(connect=False),
                member: PermissionOverwrite(manage_channels=True, connect=True, move_members=True),
            }
            channel: VoiceChannel = await after.channel.category.create_voice_channel(
                f"{member.display_name}'s channel", overwrites=overwrites
            )
            await member.move_to(channel)
            await private_voice.set_private_voice_channel(member.id, channel.id)
            return

        if before.channel:
            await self._check_channel(member, before, private_voice)

    async def _check_channel(
        self, member: Member, before: VoiceState, private_voice: GuildPrivateVoice
    ):
        if not (channel_id := private_voice.active_channels.get(str(member.id))):
            return
        if before.channel.id != channel_id:
            return
        if not before.channel.members:
            await before.channel.delete()
            await private_voice.delete_private_voice_channel(member.id)
            return

        first_member = before.channel.members[0]
        await private_voice.set_private_voice_channel(first_member.id, before.channel.id)
        await before.channel.set_permissions(
            member, manage_channels=False, connect=False, move_members=False
        )
        await before.channel.set_permissions(
            first_member, manage_channels=True, connect=True, move_members=True
        )

    @Cog.listener()
    @cog_is_enabled()
    async def on_button_click(self, ctx: ComponentContext):
        if not ctx.custom_id.startswith("voice"):
            return

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        active_channels = guild_data.private_voice.active_channels
        content = get_content("PRIVATE_VOICE", guild_data.configuration.language)
        if str(ctx.author_id) not in active_channels:
            return await ctx.send(content["DONT_HAVE_PRIVATE_ROOM"], hidden=True)

        voice_channel: VoiceChannel = ctx.guild.get_channel(active_channels[str(ctx.author_id)])
        match ctx.custom_id:
            case "voice_close":
                await voice_channel.set_permissions(ctx.guild.default_role, connect=False)
                await ctx.send(content["ROOM_CLOSED"], hidden=True)
            case "voice_open":
                await voice_channel.set_permissions(ctx.guild.default_role, connect=True)
                await ctx.send(content["ROOM_OPENED"], hidden=True)
            case "voice_hide":
                await voice_channel.set_permissions(ctx.guild.default_role, view_channel=False)
                await ctx.send(content["ROOM_HIDED"], hidden=True)
            case "voice_unhide":
                await voice_channel.set_permissions(ctx.guild.default_role, view_channel=True)
                await ctx.send(content["ROOM_UNHIDED"], hidden=True)
            case "voice_change_room_name":
                modal = Modal(
                    custom_id="voice_modal_change_room_name",
                    title=content["PRIVATE_ROOM_CONTROL_MODAL"],
                    components=[
                        TextInput(
                            custom_id="channel_name",
                            label=content["ROOM_NAME"],
                            style=TextInputStyle.SHORT,
                        )
                    ],
                )
                await ctx.popup(modal)
            case "voice_ban" | "voice_unban" | "voice_kick" | "voice_transfer":
                modal = Modal(
                    custom_id=f"voice_modal_{ctx.custom_id.replace('voice', '')}",
                    title=content["PRIVATE_ROOM_CONTROL_MODAL"],
                    components=[
                        TextInput(
                            custom_id="user_id",
                            label=content["MEMBER_ID"],
                            style=TextInputStyle.SHORT,
                        )
                    ],
                )
                await ctx.popup(modal)
            case "voice_set_room_limit":
                select = Select(
                    custom_id="voice_select_set_room_limit",
                    options=[
                        SelectOption(label=content["REMOVE_LIMIT"], value=0),
                        SelectOption(label="2", value=2),
                        SelectOption(label="3", value=3),
                        SelectOption(label="4", value=4),
                        SelectOption(label="5", value=5),
                        SelectOption(label="10", value=10),
                    ],
                )
                await ctx.send(content["SETUP_ROOM_LIMIT"], components=[select], hidden=True)

    @Cog.listener()
    @cog_is_enabled()
    async def on_select_option(self, ctx: ComponentContext):
        if not ctx.custom_id.startswith("voice"):
            return

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        active_channels = guild_data.private_voice.active_channels
        content = get_content("PRIVATE_VOICE", guild_data.configuration.language)
        if str(ctx.author_id) not in active_channels:
            return await ctx.send(content["DONT_HAVE_PRIVATE_ROOM"], hidden=True)

        voice_channel: VoiceChannel = ctx.guild.get_channel(active_channels[str(ctx.author_id)])

        await voice_channel.edit(user_limit=ctx.values[0])
        await ctx.send(content["LIMIT_WAS_SETUP"], hidden=True)

    @Cog.listener(name="on_modal")
    @cog_is_enabled()
    async def on_voice_modal(self, ctx: ModalContext):
        if not ctx.custom_id.startswith("voice"):
            return

        await ctx.defer(hidden=True)

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        voice_channel_id = guild_data.private_voice.active_channels.get(str(ctx.author_id))
        content = get_content("PRIVATE_VOICE", guild_data.configuration.language)
        if voice_channel_id is None:
            return await ctx.send(content["DONT_HAVE_PRIVATE_ROOM"], hidden=True)

        voice_channel: VoiceChannel = ctx.guild.get_channel(voice_channel_id)

        if channel_name := ctx.values.get("channel_name"):
            await voice_channel.edit(name=channel_name)
            return await ctx.send(content["ROOM_NAME_WAS_SETUP"], hidden=True)

        user_id: str = ctx.values["user_id"]
        if not user_id.isdigit():
            return await ctx.send(content["NOT_ID"], hidden=True)

        member: Member = ctx.guild.get_member(int(user_id))
        if member is None:
            return await ctx.send(content["NOT_MEMBER_ID"], hidden=True)

        match ctx.custom_id:
            case "voice_modal_ban":
                await voice_channel.set_permissions(member, connect=False)
                if member.voice and member.voice.channel.id == voice_channel_id:
                    await member.move_to(None)
                await ctx.send(content["MEMBER_WAS_BANNED"], hidden=True)
            case "voice_modal_unban":
                await voice_channel.set_permissions(member, connect=True)
                await ctx.send(content["MEMBER_WAS_UNBANNED"], hidden=True)
            case "voice_modal_kick":
                if member.voice and member.voice.channel.id == voice_channel_id:
                    await member.move_to(None)
                await ctx.send(content["MEMBER_WAS_KICKED"], hidden=True)
            case "voice_modal_transfer":
                await guild_data.private_voice.set_private_voice_channel(user_id, voice_channel_id)
                await voice_channel.set_permissions(
                    member, manage_channels=True, connect=True, move_members=True
                )
                await voice_channel.set_permissions(
                    ctx.author, manage_channels=False, connect=False, move_members=False
                )
                await ctx.send(content["OWNERSHIP_TRANSFERED"], hidden=True)


def setup(bot):
    bot.add_cog(PrivateRooms(bot))
