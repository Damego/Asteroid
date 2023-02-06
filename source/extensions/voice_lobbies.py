from typing import Final

from interactions import (
    ActionRow,
    Button,
    ButtonStyle,
    Channel,
    ChannelType,
    Color,
    Embed,
    Extension,
    Member,
    Overwrite,
    Permissions,
    VoiceState,
    option,
)

from core import Asteroid, BotException, GuildVoiceLobbies, MissingPermissions, command, listener
from core.context import CommandContext
from utils import try_run

VOICE_CHANNEL_OWNER_PERMISSIONS: Final = (
    Permissions.MANAGE_CHANNELS
    | Permissions.MOVE_MEMBERS
    | Permissions.VIEW_CHANNEL
    | Permissions.MUTE_MEMBERS
    | Permissions.DEAFEN_MEMBERS
    | Permissions.MANAGE_ROLES  # It's Manage Permissions for channel.
)


class VoiceLobbies(Extension):
    def __init__(self, client: Asteroid):
        self.client: Asteroid = client

    @listener
    async def on_voice_state_update(self, before: VoiceState, after: VoiceState):
        if before and before.channel_id == after.channel_id:
            return  # Ignore muting and deafening.

        guild_data = await self.client.database.get_guild(after.guild_id)
        if not guild_data.voice_lobbies:
            return
        voice_lobbies = guild_data.voice_lobbies
        if after.channel_id == voice_lobbies.voice_channel_id:
            if before and before.channel_id:
                # Rejoined to main channel from own channel.
                # I think better remove old channel and create a new one
                # because user can break own channel somehow
                await self._remove_transfer_voice_lobby(before, after, voice_lobbies)

            guild = await after.get_guild()
            member = await self.client.get_member(after.guild_id, after.user_id)

            permissions = [
                Overwrite(
                    id=int(member.id),
                    type=1,
                    allow=VOICE_CHANNEL_OWNER_PERMISSIONS,
                )
            ]
            if voice_lobbies.private_lobbies:
                permissions.append(
                    Overwrite(id=int(guild.id), type=0, deny=Permissions.VIEW_CHANNEL)
                )
            channel = await guild.create_channel(
                member.name[:100],
                ChannelType.GUILD_VOICE,
                parent_id=voice_lobbies.category_channel_id,
                permission_overwrites=permissions,
            )
            await member.modify(guild_id=guild.id, channel_id=channel.id)

            voice_lobbies.add_channel(int(channel.id), int(member.id))
            await voice_lobbies.update()

            return

        await self._remove_transfer_voice_lobby(before, after, voice_lobbies)
        await self._cleanup_voice_lobbies(voice_lobbies)

    async def _remove_transfer_voice_lobby(
        self, before: VoiceState, after: VoiceState, voice_lobbies: GuildVoiceLobbies
    ):
        """
        Removes previous user channel or takes ownership to another channel member, if channel exists.
        """
        if not before or not before.channel_id:
            return

        lobby = voice_lobbies.get_lobby(int(before.channel_id))
        if not lobby:
            return

        channel = await self.client.get_channel(before.channel_id)
        if not channel.voice_states:
            await channel.delete()
            voice_lobbies.remove_lobby(int(before.channel_id))
            await voice_lobbies.update()
            return

        first_voice_state: VoiceState = channel.voice_states[0]
        lobby.owner_id = int(first_voice_state.user_id)
        permissions = [
            Overwrite(
                id=int(after.user_id),
                type=1,
                deny=VOICE_CHANNEL_OWNER_PERMISSIONS,
            ),
            Overwrite(
                id=int(first_voice_state.user_id),
                type=1,
                allow=VOICE_CHANNEL_OWNER_PERMISSIONS,
            ),
        ]
        for permission in channel.permission_overwrites:
            if permission.id == after.guild_id:
                # Don't remove perms of everyone role
                permissions.append(permission)
                break
        await channel.modify(permission_overwrites=permissions)
        await voice_lobbies.update()

    async def _cleanup_voice_lobbies(self, voice_lobbies: GuildVoiceLobbies):
        """
        Removes channels if they somehow don't were removed.
        """
        remove: bool = False
        for lobby in voice_lobbies.active_channels:
            channel: Channel = await try_run(self.client.get_channel, lobby.channel_id)
            if channel:
                if channel.voice_states:
                    continue
                await try_run(channel.delete)
            voice_lobbies.remove_lobby(lobby.channel_id)
            remove = True

        if remove:
            await voice_lobbies.update()

    @command()
    async def voice(self, ctx: CommandContext):
        """Command for the voice stuff"""
        await ctx.defer(ephemeral=True)

    @voice.subcommand()
    @option("Name for voice channel. Can be edited later.")
    @option("Should be lobbies are private by default? Can be edited later.")
    @option("Creates the special channel to control lobbies")
    async def setup(
        self,
        ctx: CommandContext,
        channel_name: str = None,
        private_lobbies: bool = False,
        create_menu_channel: bool = True,
    ):
        """Setup voice lobbies on your server"""
        if Permissions.MANAGE_GUILD not in ctx.author.permissions:
            raise MissingPermissions(Permissions.MANAGE_GUILD)

        guild = await self.client.get_guild(ctx.guild_id)
        voice_lobbies_text = ctx.translate("VOICE_LOBBIES_CHANNEL")
        create_lobby_text = ctx.translate("VOICE_LOBBIES_CREATE")

        category_channel = await guild.create_channel(
            voice_lobbies_text, ChannelType.GUILD_CATEGORY
        )
        voice_channel = await guild.create_channel(
            channel_name or create_lobby_text, ChannelType.GUILD_VOICE, parent_id=category_channel
        )
        text_channel = None
        if create_menu_channel:
            control_text = ctx.translate("VOICE_LOBBIES_CONTROL_CENTER")
            text_channel = await guild.create_channel(
                control_text, ChannelType.GUILD_TEXT, parent_id=category_channel
            )
            await self._send_control_menu(ctx, text_channel)

        await self.client.database.setup_voice_lobbies(
            ctx.guild_id,
            category_channel.id,
            voice_channel.id,
            text_channel.id if text_channel else None,
            private_lobbies,
        )
        await ctx.send(ctx.translate("VOICE_LOBBIES_READY"))

    @voice.group()
    async def lobby(self, ctx: CommandContext):
        """Lobby subcommand group option"""

    @lobby.subcommand()
    @option("The member to block")
    async def block_member(self, ctx: CommandContext, member: Member):
        """Blocks the member from your lobby"""
        if ctx.author.id == member.id:
            raise BotException("CANT_UN_BLOCK_YOURSELF")

        channel = await self.__get_lobby_channel(ctx)
        self.__set_overwrite(
            channel.permission_overwrites,
            id=int(member.id),
            type=1,
            deny=Permissions.VIEW_CHANNEL,
            allow=0,
            add_new_overwrite=True,
        )

        await channel.modify(permission_overwrites=channel.permission_overwrites)

        translate = ctx.translate("VOICE_MEMBER_BLOCKED", member.mention)
        await ctx.send(translate)

    @lobby.subcommand()
    @option("The member to unblock")
    async def unblock_member(self, ctx: CommandContext, member: Member):
        """Unblocks member of your lobby"""
        if ctx.author.id == member.id:
            raise BotException("CANT_UN_BLOCK_YOURSELF")

        channel = await self.__get_lobby_channel(ctx)
        self.__set_overwrite(
            channel.permission_overwrites,
            id=int(member.id),
            type=1,
            deny=0,
            allow=Permissions.VIEW_CHANNEL,
            add_new_overwrite=True,
        )

        await channel.modify(permission_overwrites=channel.permission_overwrites)

        translate = ctx.translate("VOICE_MEMBER_UNBLOCKED", member.mention)
        await ctx.send(translate)

    @lobby.subcommand()
    @option("Hide?")
    async def toggle_hidden(self, ctx: CommandContext, hide: bool):
        """Toggle hidden status of your lobby"""
        channel = await self.__get_lobby_channel(ctx)

        allow = Permissions.VIEW_CHANNEL if not hide else 0
        deny = Permissions.VIEW_CHANNEL if hide else 0
        self.__set_overwrite(
            channel.permission_overwrites, id=int(ctx.guild_id), type=0, deny=deny, allow=allow
        )

        await channel.modify(permission_overwrites=channel.permission_overwrites)

        translate = ctx.translate("VOICE_LOBBY_HIDE_OFF" if hide else "VOICE_LOBBY_HIDE_OFF")
        await ctx.send(translate)

    @lobby.subcommand()
    @option("The new lobby name")
    async def change_name(self, ctx: CommandContext, name: str):
        """Changes name of your lobby"""
        channel = await self.__get_lobby_channel(ctx)

        await channel.modify(name=name)

    @lobby.subcommand()
    @option("The new owner of lobby")
    async def transfer_ownership(self, ctx: CommandContext, member: Member):
        """Changes name of your lobby"""
        if ctx.author.id == member.id:
            raise BotException("CANT_GIVE_OWNERSHIP_TO_SELF")

        channel = await self.__get_lobby_channel(ctx)
        self.__set_overwrite(
            channel.permission_overwrites,
            id=int(ctx.author.id),
            type=1,
            deny=VOICE_CHANNEL_OWNER_PERMISSIONS,
        )
        self.__set_overwrite(
            channel.permission_overwrites,
            id=int(member.id),
            type=1,
            allow=VOICE_CHANNEL_OWNER_PERMISSIONS,
        )

        await channel.modify(permission_overwrites=channel.permission_overwrites)

        guild_data = await self.client.database.get_guild(ctx.guild_id)
        lobby = guild_data.voice_lobbies.get_lobby(int(channel.id))
        lobby.owner_id = int(member.id)

        await guild_data.voice_lobbies.update()

        translate = ctx.translate("VOICE_LOBBY_OWNERSHIP_TRANSFERRED", member.mention)
        await ctx.send(translate)

    async def _send_control_menu(self, ctx: CommandContext, channel: Channel):
        translate = ctx.translate

        close_open = translate("VOICE_BTN_CLOSE_OPEN")
        rename = translate("VOICE_BTN_RENAME")
        set_limit = translate("VOICE_BTN_SET_LIMIT")
        ban_member = translate("VOICE_BTN_BAN")
        unban_member = translate("VOICE_BTN_UNBAN")
        transfer_ownership = translate("TRANSFER_OWNERSHIP")

        # TODO: Replace labels to emojis
        components = [
            ActionRow(
                components=[
                    Button(
                        label=close_open, custom_id="vl|toggle-close", style=ButtonStyle.PRIMARY
                    ),
                    Button(label=rename, custom_id="vl|rename", style=ButtonStyle.PRIMARY),
                    Button(label=set_limit, custom_id="vl|set-limit", style=ButtonStyle.PRIMARY),
                ]
            ),
            ActionRow(
                components=[
                    Button(label=ban_member, custom_id="vl|ban-user", style=ButtonStyle.PRIMARY),
                    Button(
                        label=unban_member, custom_id="vl|unban-user", style=ButtonStyle.PRIMARY
                    ),
                    Button(
                        label=transfer_ownership,
                        custom_id="vl|transfer-ownership",
                        style=ButtonStyle.PRIMARY,
                    ),
                ]
            ),
        ]
        embed = Embed(
            title=translate("VOICE_ROOM_MANAGE_EMBED_TITLE"),
            description="",  # TODO: add text like (emoji: what button with this emoji does)
            color=Color.BLURPLE,
        )
        await channel.send(embeds=embed, components=components)

    async def __get_lobby_channel(self, ctx: CommandContext) -> Channel:
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        voice_lobbies = guild_data.voice_lobbies

        if not voice_lobbies:
            raise BotException("VOICE_NOT_SETUP")
        user_lobby = voice_lobbies.get_lobby(owner_id=int(ctx.author.id))
        if not user_lobby:
            raise BotException("DONT_HAVE_LOBBY")

        return await self.client.get_channel(user_lobby.channel_id)

    @staticmethod
    def __set_overwrite(
        overwrites: list[Overwrite],
        *,
        id: int,
        type: int,
        allow: Permissions | int = 0,
        deny: Permissions | int = 0,
        add_new_overwrite: bool = False,
    ):
        overwrite = Overwrite(id=id, type=type, allow=allow, deny=deny)
        if add_new_overwrite:
            overwrites.append(overwrite)
            return

        for i, overwrite in enumerate(overwrites):
            if overwrite.id == id:
                overwrites[i] = overwrite


def setup(client):
    VoiceLobbies(client)
