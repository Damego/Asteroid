from discord import User, Member, Embed, Role
from discord.ext.commands import has_guild_permissions
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand

from my_utils import AsteroidBot, get_content, Cog


class Moderation(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = 900384185804525678
        self.name = 'Moderation'

    @slash_subcommand(
        base='mod',
        name='mute',
        description='Mute member'
    )
    @has_guild_permissions(mute_members=True)
    async def mute(self, ctx: SlashContext, member: Member, reason: str = None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('FUNC_MODERATION_MUTE_MEMBER', lang)

        if member.bot:
            return await ctx.send(content['CANNOT_MUTE_BOT_TEXT'], hidden=True)

        was_muted = content['WAS_MUTED_TEXT'].format(member.mention)
        mute_reason = content['REASON_TEXT'].format(reason=reason)

        muted_role = self.get_muted_role(ctx)
        await member.add_roles(muted_role, reason=reason)
        message_content = was_muted
        if reason:
            message_content += f"\n{mute_reason}"

        await ctx.send(message_content)

    @slash_subcommand(
        base='mod',
        name='create_muted_role',
        description='Creates muted role'
    )
    async def create_muted_role(self, ctx: SlashContext, role_name: str):
        await ctx.defer()
        muted_role = await ctx.guild.create_role(name=role_name)
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)

        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        collection.update_one(
            {'_id': 'configuration'},
            {
                '$set': {
                    'muted_role': muted_role.id
                },
            },
            upsert=True
        )
        content = get_content('FUNC_MODERATION_MUTE_MEMBER', lang=self.bot.get_guild_bot_lang(ctx.guild_id))
        await ctx.send(content['MUTED_ROLE_CREATED_TEXT'.format(role_name=muted_role.name)])

    def get_muted_role(self, ctx: SlashContext):
        collection = self.bot.get_guild_configuration_collection(ctx.guild_id)
        guild_data = collection.find_one({'_id': 'configuration'})
        return ctx.guild.get_role(guild_data.get('muted_role'))

    @slash_subcommand(
        base='mod',
        name='unmute',
        description='Unmute members'
    )
    @has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: SlashContext, member: Member):
        muted_role = self.get_muted_role(ctx)
        await member.remove_roles(muted_role)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='mod',
        name='ban',
        description='Ban member'
    )
    @has_guild_permissions(ban_members=True)
    async def ban(self, ctx: SlashContext, member: Member, reason: str = None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('FUNC_MODERATION_BAN_MEMBER', lang)
        if member.bot:
            return await ctx.send(content['CANNOT_BAN_BOT_TEXT'], hidden=True)

        await member.ban(reason=reason)
        was_banned_text = content['WAS_BANNED_TEXT'].format(member=member)
        ban_reason_text = content['REASON_TEXT'].format(member=member)
        embed = Embed(
            title=was_banned_text,
            description=ban_reason_text,
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        await ctx.send(embed=embed)
        embed.description += content['SERVER'].format(guild=ctx.guild)
        await member.send(embed=embed)

    @slash_subcommand(
        base='mod',
        name='unban',
        description='Unban member'
    )
    @has_guild_permissions(ban_members=True)
    async def unban(self, ctx: SlashContext, user: User):
        await ctx.guild.unban(user)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='mod',
        name='kick',
        description='Kick member'
    )
    @has_guild_permissions(kick_members=True)
    async def kick(self, ctx: SlashContext, member: Member, reason: str = None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('FUNC_MODERATION_KICK_MEMBER', lang)
        if member.bot:
            return await ctx.send(content['CANNOT_KICK_BOT_TEXT'], hidden=True)

        await member.kick(reason=reason)
        was_kicked_text = content['WAS_KICKED_TEXT'].format(member=member)
        kick_reason_text = content['REASON_TEXT'].format(member=member)
        embed = Embed(
            title=was_kicked_text,
            description=kick_reason_text,
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        await ctx.send(embed=embed)
        embed.description += content['SERVER'].format(guild=ctx.guild)
        await member.send(embed=embed)

    @slash_subcommand(
        base='mod',
        name='remove_role',
        description='Remove role of member'
    )
    @has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx: SlashContext, member: Member, role: Role):
        await member.remove_roles(role)
        await ctx.send('✅', hidden=True)

    @slash_subcommand(
        base='mod',
        name='add_role',
        description='Add role to member'
    )
    @has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx: SlashContext, member: Member, role: Role):
        await member.add_roles(role)
        await ctx.send('✅', hidden=True)

    @has_guild_permissions(manage_nicknames=True)
    @slash_subcommand(
        base='mod',
        name='nick',
        description='Change nick of member'
    )
    async def nick(self, ctx: SlashContext, member: Member, new_nick: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('FUNC_MODERATION_CHANGE_NICK_TEXT', lang)

        old_nick = member.display_name
        embed = Embed(color=self.bot.get_embed_color(ctx.guild_id))
        await member.edit(nick=new_nick)
        embed.description = content.format(old_nick, new_nick)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base='mod',
        name='clear',
        description='Deletes messages in channel'
    )
    @has_guild_permissions(manage_messages=True)
    async def clear(self, ctx: SlashContext, amount: int, member: Member = None):
        def check(message):
            return message.author.id == member.id
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: dict = get_content('FUNC_MODERATION_CLEAR_MESSAGES', lang)

        await ctx.defer(hidden=True)
        await ctx.channel.purge(limit=amount+1, check=check if member else None)
        await ctx.send(content.format(amount), hidden=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
