from discord import Embed, Forbidden, Member, Role, VoiceChannel
from discord.ext.commands import bot_has_guild_permissions
from discord_slash import SlashCommandOptionType, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_option
from utils import AsteroidBot, Cog, bot_owner_or_permissions, get_content


class Moderation(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = 962648455879225344
        self.name = "Moderation"

    @slash_subcommand(
        base="mod",
        name="ban",
        description="Ban member",
        base_dm_permission=False,
    )
    @bot_owner_or_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    async def ban(self, ctx: SlashContext, member: Member, reason: str = None):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content("FUNC_MODERATION_BAN_MEMBER", lang)
        if member.bot:
            return await ctx.send(content["CANNOT_BAN_BOT_TEXT"], hidden=True)

        await member.ban(reason=reason)
        was_banned_text = content["WAS_BANNED_TEXT"].format(member=member)
        ban_reason_text = content["REASON_TEXT"].format(reason=reason)
        embed = Embed(
            title=was_banned_text,
            description=ban_reason_text,
            color=await self.bot.get_embed_color(ctx.guild_id),
        )
        await ctx.send(embed=embed)
        embed.description += content["SERVER"].format(guild=ctx.guild)
        try:
            await member.send(embed=embed)
        except Forbidden:
            return

    @slash_subcommand(base="mod", name="kick", description="Kick member")
    @bot_owner_or_permissions(kick_members=True)
    @bot_has_guild_permissions(kick_members=True)
    async def kick(self, ctx: SlashContext, member: Member, reason: str = None):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content("FUNC_MODERATION_KICK_MEMBER", lang)
        if member.bot:
            return await ctx.send(content["CANNOT_KICK_BOT_TEXT"], hidden=True)

        await member.kick(reason=reason)
        was_kicked_text = content["WAS_KICKED_TEXT"].format(member=member)
        kick_reason_text = content["REASON_TEXT"].format(reason=reason)
        embed = Embed(
            title=was_kicked_text,
            description=kick_reason_text,
            color=await self.bot.get_embed_color(ctx.guild_id),
        )
        await ctx.send(embed=embed)
        embed.description += content["SERVER"].format(guild=ctx.guild)
        try:
            await member.send(embed=embed)
        except Forbidden:
            return

    @slash_subcommand(base="mod", name="remove_role", description="Remove role of member")
    @bot_owner_or_permissions(manage_roles=True)
    @bot_has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx: SlashContext, member: Member, role: Role):
        await member.remove_roles(role)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(base="mod", name="add_role", description="Add role to member")
    @bot_owner_or_permissions(manage_roles=True)
    @bot_has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx: SlashContext, member: Member, role: Role):
        await member.add_roles(role)
        await ctx.send("✅", hidden=True)

    @bot_owner_or_permissions(manage_nicknames=True)
    @bot_has_guild_permissions(manage_nicknames=True)
    @slash_subcommand(base="mod", name="nick", description="Change nick of member")
    async def nick(self, ctx: SlashContext, member: Member, new_nick: str):
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content("FUNC_MODERATION_CHANGE_NICK_TEXT", lang)

        embed = Embed(color=await self.bot.get_embed_color(ctx.guild_id))
        await member.edit(nick=new_nick)
        embed.description = content.format(member.mention, new_nick)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="mod",
        name="clear",
        description="Deletes messages in channel",
        options=[
            create_option(
                name="amount",
                description="The amount of messages to delete",
                option_type=SlashCommandOptionType.INTEGER,
            ),
            create_option(
                name="member",
                description="The member to delete message",
                option_type=SlashCommandOptionType.USER,
                required=False,
            ),
        ],
    )
    @bot_owner_or_permissions(manage_messages=True)
    @bot_has_guild_permissions(manage_messages=True)
    async def clear(self, ctx: SlashContext, amount: int, member: Member = None):
        def check(message):
            return message.author.id == member.id

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content("FUNC_MODERATION_CLEAR_MESSAGES", lang)

        await ctx.defer(hidden=True)
        deleted_messages = await ctx.channel.purge(limit=amount, check=check if member else None)
        await ctx.send(content.format(len(deleted_messages)), hidden=True)

    @slash_subcommand(base="mod", name="move_to", description="Moves member to certain channel")
    @bot_owner_or_permissions(move_members=True)
    @bot_has_guild_permissions(move_members=True)
    async def move_member_to(self, ctx: SlashContext, member: Member, voice_channel: VoiceChannel):
        content = get_content(
            "MOD_COMMANDS_CONTENT", lang=await self.bot.get_guild_bot_lang(ctx.guild_id)
        )

        if not isinstance(voice_channel, VoiceChannel):
            return await ctx.send(content["NOT_VOICE_CHANNEL_TEXT"])
        await member.move_to(voice_channel)

        await ctx.send(":white_check_mark:", hidden=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
