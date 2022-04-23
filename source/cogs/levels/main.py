import datetime
from random import randint
from time import time

from discord import Embed, Member, Message, Role, VoiceState
from discord.ext.commands import BadArgument
from discord_slash import AutoCompleteContext, SlashCommandOptionType, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import (
    AsteroidBot,
    Cog,
    CogDisabledOnGuild,
    NoData,
    bot_owner_or_permissions,
    cog_is_enabled,
    get_content,
    is_enabled,
)
from utils.paginator import Paginator, PaginatorStyle

from ._levels import formula_of_experience, update_member


class Levels(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = 863677232239869964
        self.name = "Levels"

        self.last_user_message = {}
        self.time_factor = 10

    @Cog.listener()
    @cog_is_enabled()
    async def on_member_join(self, member: Member):
        if member.bot:
            return
        guild_data = await self.bot.mongo.get_guild_data(member.guild.id)
        await guild_data.get_user(member.id)
        if guild_data.configuration.start_level_role is not None:
            role = member.guild.get_role(guild_data.configuration.start_level_role)
            await member.add_roles(role)

    @Cog.listener()
    @cog_is_enabled()
    async def on_member_remove(self, member: Member):
        if member.bot:
            return
        guild_data = await self.bot.mongo.get_guild_data(member.guild.id)
        await guild_data.remove_user(member.id)

    @Cog.listener()
    @cog_is_enabled()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.bot:
            return

        guild_data = await self.bot.mongo.get_guild_data(member.guild.id)

        if (not before.channel) and after.channel:  # * If member join to channel
            members = after.channel.members
            if len(members) == 2:
                await guild_data.add_user_to_voice(member.id)
                await guild_data.add_user_to_voice(members[0].id)
            elif len(members) > 2:
                await guild_data.add_user_to_voice(member.id)

        elif member not in before.channel.members and (
            not after.channel
        ):  # * if member left from channel
            members = before.channel.members
            if len(members) == 1:
                await self.check_time(member)
                first_member = members[0]
                await self.check_time(first_member)
            elif len(members) > 1:
                await self.check_time(member)
        elif member not in before.channel.members and member in after.channel.members:
            # * If member moved from one channel to another
            before_members = before.channel.members
            after_members = after.channel.members

            if len(before_members) == 0 and len(after_members) > 1:
                if len(after_members) == 2:
                    await guild_data.add_user_to_voice(after_members[0].id)
                await guild_data.add_user_to_voice(member.id)

            if len(before_members) == 1:
                await self.check_time(before_members[0])
            if len(after_members) == 1:
                await self.check_time(after_members[0])

    async def check_time(self, member: Member):
        guild_data = await self.bot.mongo.get_guild_data(member.guild.id)

        voice_user = guild_data.users_voice_time.get(str(member.id))
        if voice_user is None:
            return

        total_time = int(time()) - voice_user
        earned_exp = (total_time // 60) * self.time_factor
        await update_member(self.bot, member, earned_exp)
        user_data = await guild_data.get_user(member.id)
        await user_data.increase_leveling(voice_time=total_time // 60)
        await guild_data.remove_user_to_voice(member.id)

    @Cog.listener()
    @cog_is_enabled()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        xp = randint(25, 35)
        await update_member(self.bot, message, xp)

    @slash_subcommand(
        base="levels",
        name="reset_stats",
        description="Reset level statistics of Member",
        options=[
            create_option(name="member", description="Guild Member", option_type=6, required=True)
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def reset_member_statistics(self, ctx: SlashContext, member: Member):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(member.id)
        start_level_role = guild_data.configuration.start_level_role

        if current_role_id := user_data.role:
            role = ctx.guild.get_role(current_role_id)
            await member.remove_roles(role)

        await user_data.set_leveling(
            level=1, xp=0, xp_amount=0, voice_time=0, role_id=start_level_role
        )
        await member.add_roles(ctx.guild.get_role(start_level_role))
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        name="xp",
        description="Add exp to member",
        options=[
            create_option(
                name="member",
                description="Server Member",
                option_type=SlashCommandOptionType.USER,
                required=True,
            ),
            create_option(
                name="exp",
                description="Exp to add",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
            ),
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_add_xp(self, ctx: SlashContext, member: Member, exp: int):
        if exp <= 0:
            raise BadArgument
        await ctx.defer(hidden=True)
        await update_member(self.bot, member, exp)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="add",
        description="Add Role to level",
        options=[
            create_option(
                name="level",
                description="level",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
            ),
            create_option(
                name="role",
                description="Role to level",
                option_type=SlashCommandOptionType.ROLE,
                required=True,
            ),
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def add_level_role(self, ctx: SlashContext, level: int, role: Role):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.add_level_role(level, role.id)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="remove",
        description="Remove Role of a level",
        options=[
            create_option(
                name="level",
                description="level",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
            )
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def remove_level_role(self, ctx: SlashContext, level: int):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        if str(level) not in guild_data.roles_by_level:
            raise NoData
        await guild_data.remove_level_role(level)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="replace",
        description="Replace level role to another",
        options=[
            create_option(
                name="current_level",
                description="current_level",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
                autocomplete=True,
            ),
            create_option(
                name="new_level",
                description="new_level",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
            ),
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def replace_level_role(self, ctx: SlashContext, current_level: int, new_level: int):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        try:
            await guild_data.replace_levels(current_level, new_level)
        except KeyError:
            await ctx.send("❌", hidden=True)
        await ctx.send("✅", hidden=True)

    @Cog.listener(name="on_autocomplete")
    @cog_is_enabled()
    async def level_autocomplete(self, ctx: AutoCompleteContext):
        if self.bot.get_transformed_command_name(ctx) != "levels":
            return
        choices = []
        if ctx.focused_option in ["current_level", "remove"]:
            guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
            roles_by_level = guild_data.roles_by_level
            choices = [create_choice(name=level, value=int(level)) for level in roles_by_level]
        if choices:
            await ctx.populate(choices)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="reset",
        description="Reset levels in server",
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def reset_levels(self, ctx: SlashContext):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.reset_roles_by_level()
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="list",
        description="Show list of levels in server",
    )
    @is_enabled()
    async def send_levels_list(self, ctx: SlashContext):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        roles = guild_data.roles_by_level
        if not roles:
            return await ctx.send("No level roles")

        content = ""
        for level, role in roles.items():
            if level == "_id":
                continue

            xp_amount = 0
            role = ctx.guild.get_role(role)
            for _level in range(1, int(level)):
                exp = formula_of_experience(_level)
                xp_amount += exp
            content += f"{level} — {role.mention} | EXP: {xp_amount}\n"

        embed = Embed(description=content, color=guild_data.configuration.embed_color)
        await ctx.send(embed=embed)

    @slash_subcommand(base="levels", name="clear_members_stats")
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def clear_members_stats(self, ctx: SlashContext):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)

        for member in ctx.guild.members:
            if member.bot:
                continue

            user_data = await guild_data.get_user(member.id)
            await user_data.reset_leveling()

        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="set_start_role",
        description="Set's start level role",
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_set_start_role(self, ctx: SlashContext, role: Role):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.configuration.set_start_level_role(role.id)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="delete_start_role",
        description="Delete's start level role",
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_delete_start_role(self, ctx: SlashContext):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        await guild_data.configuration.set_start_level_role(None)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        name="leaderboard",
        description="Shows top members by level",
    )
    @is_enabled()
    async def leaderboard_members(self, ctx: SlashContext):
        await ctx.defer()

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        content = get_content("LEVELS", guild_data.configuration.language)["FUNC_TOP_MEMBERS"]
        embeds = []
        embed_desc = ""
        list_for_sort = [
            (user_data.id, user_data.level, user_data.xp)
            for user_data in guild_data.users
            if user_data.level not in (0, 1)
        ]
        list_for_sort.sort(key=lambda x: (x[1], x[-1]), reverse=True)
        for count, user_data in enumerate(list_for_sort, start=1):
            member: Member = ctx.guild.get_member(int(user_data[0]))
            if member is None:
                try:
                    member: Member = await ctx.guild.fetch_member(int(user_data[0]))
                except Exception:
                    continue

            embed_desc += f"**#{count}・{member.mention}**\n╰**{content['LEVEL']}:** `{user_data[1]}` | **{content['XP']}:** `{int(user_data[2])}`\n"

            if count % 10 == 0:
                embeds.append(await self._get_embed(ctx, embed_desc, content))
                embed_desc = ""

        if embed_desc:
            embeds.append(await self._get_embed(ctx, embed_desc, content))

        if not embeds:
            return await ctx.send(content["EMPTY_LEADERBOARD"])
        if len(embeds) < 2:
            return await ctx.send(embed=embeds[0])

        paginator = Paginator(
            self.bot, ctx, style=PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds=embeds
        )
        await paginator.start()

    async def _get_embed(self, ctx: SlashContext, embed_desc: str, content: dict):
        embed = Embed(
            title=content["TOP_MEMBERS_TEXT"],
            description=embed_desc,
            color=await self.bot.get_embed_color(ctx.guild_id),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(
            text=f'{content["REQUESTED_BY_TEXT"]} {ctx.author.display_name}',
            icon_url=ctx.author.avatar_url,
        )
        return embed
