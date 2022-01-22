from typing import List

from discord import Member, Embed, Role, Guild, TextChannel, Forbidden
from discord.ext.commands import is_owner
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand

from my_utils import (
    AsteroidBot,
    Cog,
    consts,
    paginator,
    transform_permission
)


class Staff(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.name = 'Staff Commands'
        self.private_guild_id = [consts.test_global_guilds_ids]

    @slash_subcommand(
        base='staff',
        name='send_message',
        guild_ids=consts.test_global_guilds_ids
    )
    @is_owner()
    async def send_message(self, ctx: SlashContext, channel_id: str, message: str):
        if not channel_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)
        channel: TextChannel = self.bot.get_channel(int(channel_id))
        try:
            await channel.send(message)
        except Forbidden:
            await ctx.send('Unable send message to this channel!')
        else:
            await ctx.send('Successfully sent!')

    @slash_subcommand(
        base='staff',
        name='get_guild_channels',
        guild_ids=consts.test_global_guilds_ids
    )
    @is_owner()
    async def get_guilds_channels(self, ctx: SlashContext, guild_id: str):
        if not guild_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)
        guild: Guild = self.bot.get_guild(int(guild_id))
        channels: List[TextChannel] = guild.channels
        channels_data = "\n".join([f"{channel.name} | {channel.id}" for channel in channels])
        embed = Embed(title=f'Channels of {guild.name}', description=channels_data)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base='staff',
        name='get_guilds',
        guild_ids=consts.test_global_guilds_ids
    )
    async def get_guilds(self, ctx: SlashContext):
        guilds = self.bot.guilds
        embed = Embed(
            title='All bot guilds',
            description='\n'.join([f"{guild.name} | {guild.id}" for guild in guilds])
        )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="staff",
        name="get_guild_roles",
        guild_ids=consts.test_global_guilds_ids
    )
    async def get_guild_roles(self, ctx: SlashContext, guild_id: str):
        if not guild_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)
        guild: Guild = self.bot.get_guild(int(guild_id))
        guild_roles = guild.roles[::-1]
        embeds = []
        for count, role in enumerate(guild_roles, start=1):
            if count == 1:
                embed = Embed(
                    title=f'Roles of {guild.name} server',
                    description=''
                )
            if count % 25 == 0:
                embeds.append(embed)
                embed = Embed(
                    title=f'Roles of {guild.name} server',
                    description=''
                )
            embed.description += f"{role.name} | {role.id} \n"
        if embed.description:
            embeds.append(embed)

        _paginator = paginator.Paginator(self.bot, ctx, paginator.PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds)
        await _paginator.start()

    @slash_subcommand(
        base="staff",
        name="get_guild_bot_info",
        guild_ids=consts.test_global_guilds_ids
    )
    async def get_guild_bot_info(self, ctx: SlashContext, guild_id: str):
        if not guild_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)

        guild: Guild = self.bot.get_guild(int(guild_id))
        bot: Member = guild.get_member(ctx.bot.user.id)
        embed = Embed(
            title=f"Bot information on {guild.name} server"
        )
        embed.add_field(
            name="Roles",
            value=', '.join([f"`{role.name}`" for role in bot.roles]),
            inline=False,
        )

        server_info = f"**Bot's amount:** `{len([member for member in guild.members if member.bot])}`\n" \
                      f"**Total members:** `{guild.member_count}`"
        embed.add_field(
            name="Server info",
            value=server_info,
            inline=False
        )

        bot_perms = ''.join(
            f"✅ {transform_permission(permission[0])}\n" 
            if permission[1]
            else f"❌ {transform_permission(permission[0])}\n"
            for permission in bot.guild_permissions
        )

        embed.add_field(
            name="Permissions",
            value=bot_perms
        )
        try:
            server_invites = await guild.invites()
        except Forbidden:
            pass
        else:
            embed.add_field(
                name="Invites",
                value="/n".join([f"{invite}" for invite in server_invites])
            )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="staff",
        name="give_role",
        guild_ids=consts.test_global_guilds_ids
    )
    async def give_role(self, ctx: SlashContext, guild_id: str, member_id: str, role_id: str):
        if not guild_id.isdigit() or not member_id.isdigit() or not role_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)

        guild: Guild = self.bot.get_guild(int(guild_id))
        member: Member = guild.get_member(int(member_id))
        role: Role = guild.get_role(int(role_id))

        try:
            await member.add_roles(role)
        except Forbidden:
            await ctx.send("Forbidden")
        else:
            await ctx.send("Successfully")

    @slash_subcommand(
        base="staff",
        name="move_to",
        guild_ids=consts.test_global_guilds_ids
    )
    async def move_member_to(self, ctx: SlashContext, guild_id: str, member_id: str, channel_id: str):
        if not guild_id.isdigit() or not member_id.isdigit() or not channel_id.isdigit():
            return await ctx.send('INPUT NUMBER', hidden=True)

        guild: Guild = self.bot.get_guild(int(guild_id))
        member: Member = guild.get_member(int(member_id))
        channel = guild.get_channel(int(channel_id))
        try:
            await member.move_to(channel)
        except Forbidden:
            await ctx.send("Cannot move member")
        else:
            await ctx.send("Successfully")


def setup(bot: AsteroidBot):
    bot.add_cog(Staff(bot))