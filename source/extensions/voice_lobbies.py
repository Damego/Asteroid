from interactions import ChannelType, CommandContext, Extension, Overwrite, Permissions
from interactions import extension_command as command
from interactions import extension_listener as listener
from interactions import option
from interactions.ext.lavalink import VoiceState

from core import Asteroid, GuildData  # isort: skip


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
        if after.channel_id == guild_data.voice_lobbies.voice_channel_id:
            if before and before.channel_id:
                # Rejoined to main channel from own channel. For what lol?
                await self.__check_channel(before, after, guild_data)

            guild = await after.get_guild()
            member = await self.client.get_member(after.guild_id, after.user_id)

            permissions = [
                Overwrite(
                    id=int(member.id),
                    type=1,
                    allow=Permissions.MANAGE_CHANNELS | Permissions.MOVE_MEMBERS,
                )
            ]
            if guild_data.voice_lobbies.private_lobbies:
                permissions.append(
                    Overwrite(id=int(guild.id), type=0, deny=Permissions.VIEW_CHANNEL)
                )
            channel = await guild.create_channel(
                f"{member.name}'s channel",
                ChannelType.GUILD_VOICE,
                parent_id=guild_data.voice_lobbies.category_channel_id,
                permission_overwrites=permissions,
            )
            await member.modify(guild_id=guild.id, channel_id=channel.id)
            guild_data.voice_lobbies.add_channel(int(channel.id), int(member.id))
            await guild_data.voice_lobbies.update()
            return

        await self.__check_channel(before, after, guild_data)

    async def __check_channel(self, before: VoiceState, after: VoiceState, guild_data: GuildData):
        """
        Removes previous user channel or takes ownership to another channel member, if channel exists.
        """
        lobby = guild_data.voice_lobbies.get_lobby(owner_id=int(after.user_id))
        if not lobby:
            return
        if before and before.channel_id == lobby.channel_id:
            channel = await self.client.get_channel(before.channel_id)
            if not channel.voice_states:
                await channel.delete()
                guild_data.voice_lobbies.remove_lobby(int(before.channel_id))
                await guild_data.voice_lobbies.update()
                return
            first_voice_state: VoiceState = channel.voice_states[0]
            lobby.owner_id = int(first_voice_state.user_id)
            permissions = [
                Overwrite(
                    id=int(after.user_id),
                    type=1,
                    deny=Permissions.MANAGE_CHANNELS | Permissions.MOVE_MEMBERS,
                ),
                Overwrite(
                    id=int(first_voice_state.user_id),
                    type=1,
                    allow=Permissions.MANAGE_CHANNELS | Permissions.MOVE_MEMBERS,
                ),
            ]
            for permission in channel.permission_overwrites:
                if permission.id == after.guild_id:
                    # Don't remove perms of everyone role
                    permissions.append(permission)
                    break

            await channel.modify(permission_overwrites=permissions)
            await guild_data.voice_lobbies.update()

    @command()
    async def voice(self, ctx: CommandContext):
        """Base command"""
        ...

    @voice.subcommand()
    @option("Name for voice channel. Can be edited later.")
    @option("Create a text channel with control panel.")
    @option("Should be lobbies are private by default? Can be edited later.")
    async def setup(
        self,
        ctx: CommandContext,
        channel_name: str = None,
        create_text_channel: bool = False,
        private_lobbies: bool = False,
    ):
        """Setup voice lobbies on your server"""
        await ctx.defer(ephemeral=True)
        # TODO: Check author perms. Should be MANAGE_SERVER ig
        guild_data = await self.client.database.get_guild(ctx.guild_id)
        print(guild_data.voice_lobbies)
        guild = await self.client.get_guild(ctx.guild_id)
        category_channel = await guild.create_channel("Voice Lobbies", ChannelType.GUILD_CATEGORY)
        voice_channel = await guild.create_channel(
            channel_name or "Create lobby", ChannelType.GUILD_VOICE, parent_id=category_channel
        )
        text_channel = None
        if create_text_channel:
            text_channel = await guild.create_channel(
                "Lobby control", ChannelType.GUILD_TEXT, parent_id=category_channel
            )

        await self.client.database.setup_voice_lobbies(
            ctx.guild_id,
            category_channel.id,
            voice_channel.id,
            text_channel.id if text_channel else None,
            private_lobbies,
        )
        await ctx.send("Ready")


def setup(client):
    VoiceLobbies(client)
