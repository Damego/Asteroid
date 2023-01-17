from typing import Final

from interactions import (
    ActionRow,
    Button,
    ButtonStyle,
    Channel,
    ChannelType,
    CommandContext,
    Extension,
    Member,
    Overwrite,
    Permissions,
    VoiceState,
    option,
)

from core import Asteroid, BotException, GuildVoiceLobbies, MissingPermissions, command, listener

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
                # Rejoined to main channel from own channel. For what lol?
                await self.__remove_user_channel(before, after, voice_lobbies)

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
                f"{member.name}'s channel",  # TODO: Add localization
                ChannelType.GUILD_VOICE,
                parent_id=voice_lobbies.category_channel_id,
                permission_overwrites=permissions,
            )
            await member.modify(guild_id=guild.id, channel_id=channel.id)
            voice_lobbies.add_channel(int(channel.id), int(member.id))
            await voice_lobbies.update()
            return

        await self.__remove_user_channel(before, after, voice_lobbies)
        await self.__check_channels(voice_lobbies)

    async def __remove_user_channel(
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

    async def __check_channels(self, voice_lobbies: GuildVoiceLobbies):
        """
        Removes channels if they somehow don't were removed.
        """
        remove: bool = False
        for lobby in voice_lobbies.active_channels:
            channel: Channel = await self.client.try_run(self.client.get_channel, lobby.channel_id)
            if channel:
                if channel.voice_states:
                    continue
                await self.client.try_run(channel.delete)
            voice_lobbies.remove_lobby(lobby.channel_id)
            remove = True

        if remove:
            await voice_lobbies.update()

    @command()
    async def voice(self, ctx: CommandContext):
        """Base command"""
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
        category_channel = await guild.create_channel("Voice Lobbies", ChannelType.GUILD_CATEGORY)
        voice_channel = await guild.create_channel(
            channel_name or "Create lobby", ChannelType.GUILD_VOICE, parent_id=category_channel
        )
        text_channel = None
        if create_menu_channel:
            text_channel = await guild.create_channel(
                "Control", ChannelType.GUILD_TEXT, parent_id=category_channel
            )
            await self.__send_control_menu(text_channel)

        await self.client.database.setup_voice_lobbies(
            ctx.guild_id,
            category_channel.id,
            voice_channel.id,
            text_channel.id if text_channel else None,
            private_lobbies,
        )
        await ctx.send("Ready")

    @voice.group()
    async def lobby(self, ctx: CommandContext):
        """Group command"""

    @lobby.subcommand()
    @option("The member to block")
    async def block_member(self, ctx: CommandContext, member: Member):
        """Blocks the member from your lobby"""
        if ctx.author.id == member.id:
            raise BotException(203)

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

        await ctx.send(f"You blocked {member.mention}!")

    @lobby.subcommand()
    @option("The member to unblock")
    async def unblock_member(self, ctx: CommandContext, member: Member):
        """Unblocks member of your lobby"""
        if ctx.author.id == member.id:
            raise BotException(203)

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

        await ctx.send(f"You unblocked {member.mention}!")

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

        _hide_text = "was hided" if hide else "was unhide"
        await ctx.send(f"Your lobby {_hide_text}!")

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
            raise BotException(204)

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

    async def __send_control_menu(self, channel: Channel):
        components = [
            ActionRow(
                components=[
                    Button(
                        label="CLOSE/OPEN", custom_id="vl|toggle-close", style=ButtonStyle.PRIMARY
                    ),
                    Button(label="RENAME", custom_id="vl|rename", style=ButtonStyle.PRIMARY),
                    Button(label="SET LIMIT", custom_id="vl|set-limit", style=ButtonStyle.PRIMARY),
                ]
            ),
            ActionRow(
                components=[
                    Button(label="BAN", custom_id="vl|close-room", style=ButtonStyle.PRIMARY),
                    Button(label="UNBAN", custom_id="vl|close-room", style=ButtonStyle.PRIMARY),
                    Button(label="CLOSE", custom_id="vl|close-room", style=ButtonStyle.PRIMARY),
                    Button(label="CLOSE", custom_id="vl|close-room", style=ButtonStyle.PRIMARY),
                    Button(label="CLOSE", custom_id="vl|close-room", style=ButtonStyle.PRIMARY),
                ]
            ),
        ]
        # embed = Embed(
        #     title="You could manage your room via these buttons",
        #     description="",  # TODO: add text like (emoji: what button with this emoji does)
        #     color=Color.BLURPLE
        # )
        # message =
        await channel.send(components=components)

    async def __get_lobby_channel(self, ctx: CommandContext) -> Channel:
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        voice_lobbies = guild_data.voice_lobbies

        if not voice_lobbies:
            raise BotException(201)
        user_lobby = voice_lobbies.get_lobby(owner_id=int(ctx.author.id))
        if not user_lobby:
            raise BotException(202)

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
        for i, overwrite in enumerate(overwrites):
            if overwrite.id == id:
                overwrites[i] = overwrite  # Mixins...
        if not add_new_overwrite:
            return
        overwrites.append(overwrite)


def setup(client):
    VoiceLobbies(client)
