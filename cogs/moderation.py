from asyncio.tasks import sleep
import discord
from discord.ext import commands
from discord_slash import ComponentContext, MenuContext, ContextMenuType
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand,
    cog_context_menu as context_menu
)

from my_utils import AsteroidBot
from my_utils import get_content
from .settings import DurationConverter, multiplier, guild_ids



class Moderation(commands.Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🛡️'


    @slash_subcommand(
        base='mod',
        name='mute',
        description='Mute member',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx: ComponentContext, member: discord.Member, duration: DurationConverter, *, reason=None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: str = get_content('FUNC_MODERATION_MUTE_MEMBER', lang)

        if member.bot:
            return await ctx.send(content['CANNOT_MUTE_BOT_TEXT'], hidden=True)

        amount, time_format = duration

        was_muted = content['WAS_MUTED_TEXT'].format(member.mention)
        muted_time = content['TIME_TEXT'].format(amount=amount, time_format=time_format)
        mute_reason = content['REASON_TEXT'].format(reason=reason)
        amount, time_format = duration
        
        muted_role = await self.get_muted_role(ctx)
        await member.add_roles(muted_role, reason=reason)
        embed = discord.Embed(title=was_muted, color=self.bot.get_embed_color(ctx.guild.id))
        _description = muted_time

        if reason is not None:
            _description += mute_reason
        embed.description = _description
        await ctx.send(embed=embed)

        await sleep(amount * multiplier[time_format])
        await member.remove_roles(muted_role)
        
    async def get_muted_role(self, ctx):
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
        if not muted_role:
            muted_role = await ctx.guild.create_role(name='Muted')

            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
                await sleep(0.05)
        return muted_role


    @slash_subcommand(
        base='mod',
        name='unmute',
        description='Unmute members',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: ComponentContext, member:discord.Member):
        muted_role = await self.get_muted_role(ctx)
        await member.remove_roles(muted_role)
        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='mod',
        name='ban',
        description='Ban member',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: ComponentContext, member:discord.Member, *, reason=None):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: str = get_content('FUNC_MODERATION_BAN_MEMBER', lang)
        if member.bot:
            return await ctx.send(content['CANNOT_BAN_BOT_TEXT'], hidden=True)

        await member.ban(reason=reason)
        was_banned_text = content['WAS_BANNED_TEXT'].format(member=member)
        ban_reason_text = content['REASON_TEXT'].format(member=member)
        embed = discord.Embed(
            title=was_banned_text,
            description=ban_reason_text,
            color=self.bot.get_embed_color(ctx.guild.id)
        )
        await ctx.send(embed=embed)
        embed.description += content['SERVER'].format(guild=ctx.guild)
        await member.send(embed=embed)


    @slash_subcommand(
        base='mod',
        name='unban',
        description='Unban member',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx:ComponentContext, user: discord.User):
        await ctx.guild.unban(user)
        await ctx.message.add_reaction('✅')

                    
    @slash_subcommand(
        base='mod',
        name='kick',
        description='Kick member',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx: ComponentContext, member: discord.Member, reason: str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: str = get_content('FUNC_MODERATION_KICK_MEMBER', lang)
        if member.bot:
            return await ctx.send(content['CANNOT_KICK_BOT_TEXT'], hidden=True)

        await member.kick(reason=reason)
        was_kicked_text = content['WAS_KICKED_TEXT'].format(member=member)
        kick_reason_text = content['REASON_TEXT'].format(member=member)
        embed = discord.Embed(
            title=was_kicked_text,
            description=kick_reason_text,
            color=self.bot.get_embed_color(ctx.guild.id)
        )
        await ctx.send(embed=embed)
        embed.description += content['SERVER'].format(guild=ctx.guild)
        await member.send(embed=embed)


    @slash_subcommand(
        base='mod',
        name='remove_role',
        description='Remove role of member',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx: ComponentContext, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='mod',
        name='add_role',
        description='Add role to member',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx: ComponentContext, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await ctx.message.add_reaction('✅')


    @commands.has_guild_permissions(manage_nicknames=True)
    @slash_subcommand(
        base='mod',
        name='nick',
        description='Change nick of member',
        guild_ids=guild_ids
    )
    async def nick(self, ctx: ComponentContext, member: discord.Member, new_nick:str):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: str = get_content('FUNC_MODERATION_CHANGE_NICK_TEXT', lang)

        old_nick = member.display_name
        embed = discord.Embed(color=self.bot.get_embed_color(ctx.guild.id))
        await member.edit(nick=new_nick)
        embed.description = content.format(old_nick, new_nick)
        await ctx.send(embed=embed)


    @slash_subcommand(
        base='mod',
        name='clear',
        description='Deletes messages in channel',
        guild_ids=guild_ids
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx: ComponentContext, amount: int):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content: str = get_content('FUNC_MODERATION_CLEAR_MESSAGES', lang)
        await ctx.channel.purge(limit=amount+1)
        await ctx.send(content.format(amount), delete_after=5)



def setup(bot):
    bot.add_cog(Moderation(bot))