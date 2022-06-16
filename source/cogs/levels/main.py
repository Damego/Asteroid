import datetime
from random import randint
from time import time

from discord import Embed, Forbidden, HTTPException, Member, Message, Role, VoiceState
from discord_slash import AutoCompleteContext, SlashCommandOptionType, SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash.utils.manage_commands import create_choice, create_option
from utils import (
    AsteroidBot,
    Cog,
    NoData,
    bot_owner_or_permissions,
    cog_is_enabled,
    format_voice_time,
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
        guild_data = await self.bot.get_guild_data(member.guild.id)
        await guild_data.get_user(member.id)
        if guild_data.configuration.start_level_role is not None:
            role = member.guild.get_role(guild_data.configuration.start_level_role)
            await member.add_roles(role)

    @Cog.listener()
    @cog_is_enabled()
    async def on_member_remove(self, member: Member):
        if member.bot:
            return
        guild_data = await self.bot.get_guild_data(member.guild.id)
        await guild_data.remove_user(member.id)

    @Cog.listener()
    @cog_is_enabled()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.bot:
            return

        guild_data = await self.bot.get_guild_data(member.guild.id)

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
                if not first_member.bot:
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
        guild_data = await self.bot.get_guild_data(member.guild.id)

        voice_user = guild_data.users_voice_time.get(str(member.id))
        if voice_user is None:
            return

        total_time = int(time()) - voice_user
        earned_exp = (total_time // 60) * self.time_factor
        await update_member(self.bot, member, earned_exp)
        user_data = await guild_data.get_user(member.id)
        await user_data.increase_leveling(voice_time=total_time // 60)
        await guild_data.remove_user_from_voice(member.id)

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
    async def levels_reset__stats(self, ctx: SlashContext, member: Member):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(member.id)
        start_level_role = guild_data.configuration.start_level_role

        if current_role_id := user_data.leveling.role:
            role = ctx.guild.get_role(current_role_id)
            await member.remove_roles(role)

        await user_data.set_leveling(
            level=1, xp=0, xp_amount=0, voice_time=0, role_id=start_level_role
        )
        await member.add_roles(ctx.guild.get_role(start_level_role))
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        name="add_xp",
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
                min_value=1,
                autocomplete=True,
            ),
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_add__xp(self, ctx: SlashContext, member: Member, exp: int):
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
                min_value=2,
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
    async def levels_role_add(self, ctx: SlashContext, level: int, role: Role):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
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
                min_value=1,
                autocomplete=True,
            )
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def remove_level_role(self, ctx: SlashContext, level: int):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
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
                min_value=2,
            ),
            create_option(
                name="new_level",
                description="new_level",
                option_type=SlashCommandOptionType.INTEGER,
                required=True,
                min_value=2,
            ),
        ],
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_role_replace(self, ctx: SlashContext, current_level: int, new_level: int):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        try:
            await guild_data.replace_levels(current_level, new_level)
        except KeyError:
            await ctx.send("❌", hidden=True)
        await ctx.send("✅", hidden=True)

    @Cog.listener(name="on_autocomplete")
    @cog_is_enabled()
    async def level_autocomplete(self, ctx: AutoCompleteContext):
        if ctx.name != "levels":
            return
        choices = []
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        if ctx.focused_option in ["current_level", "level"]:
            choices = [
                create_choice(name=level, value=int(level)) for level in guild_data.roles_by_level
            ]
        elif ctx.focused_option == "exp":
            user_data = await guild_data.get_user(int(ctx.options["member"]))
            user_current_level = user_data.leveling.level
            exp = 0
            for level in range(user_current_level + 1, user_current_level + 26):
                exp += formula_of_experience(level)
                choices.append(create_choice(name=f"{exp} exp to {level} level", value=exp))

        await ctx.populate(choices)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="reset",
        description="Reset levels in server",
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_role_reset(self, ctx: SlashContext):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        await guild_data.reset_roles_by_level()
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="list",
        description="Show list of levels in server",
    )
    @is_enabled()
    async def levels_role_list(self, ctx: SlashContext):
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
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
    async def levels_clear__members__stats(self, ctx: SlashContext):
        await ctx.defer(hidden=True)

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        start_role = ctx.guild.get_role(guild_data.configuration.start_level_role)
        for member in ctx.guild.members:
            if member.bot:
                continue

            user_data = await guild_data.get_user(member.id)
            current_role = ctx.guild.get_role(user_data.leveling.role)
            try:
                await member.remove_roles(current_role)
            except (Forbidden, HTTPException):
                pass
            await user_data.set_leveling(
                level=1, xp=0, xp_amount=0, role=guild_data.configuration.start_level_role
            )
            await member.add_roles(start_role)

        await ctx.send("✅", hidden=True)  # TODO: Add text

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
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        await guild_data.configuration.set_start_level_role(role.id)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="role",
        name="delete_start_role",
        description="Deletes start level role",
    )
    @is_enabled()
    @bot_owner_or_permissions(manage_guild=True)
    async def levels_role_delete__start__role(self, ctx: SlashContext):
        await ctx.defer(hidden=True)
        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        await guild_data.configuration.set_start_level_role(None)
        await ctx.send("✅", hidden=True)

    @slash_subcommand(
        base="levels",
        subcommand_group="leaderboard",
        name="by_level",
        description="Shows top members by level",
    )
    @is_enabled()
    async def levels_leaderboard_by__level(self, ctx: SlashContext):
        def simple(key):
            return self._get_embed(
                ctx, guild_data.configuration.embed_color, embed_desc, content, key
            )

        await ctx.defer()

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("LEVELS", guild_data.configuration.language)["LEADERBOARD"]
        embeds = []
        embed_desc = ""
        list_for_sort = [
            (user_data.id, user_data.leveling.level, user_data.leveling.xp)
            for user_data in guild_data.users
            if user_data.leveling.level not in (0, 1)
        ]
        list_for_sort.sort(key=lambda x: (x[1], x[-1]), reverse=True)
        for count, user_data in enumerate(list_for_sort, start=1):
            embed_desc += (
                f"**#{count}・<@{user_data[0]}>**\n╰**{content['LEVEL']}:** "
                f"`{user_data[1]}` | **{content['XP']}:** `{int(user_data[2])}`\n"
            )

            if count % 10 == 0:
                embeds.append(simple("TOP_MEMBERS_BY_LEVEL_TEXT"))
                embed_desc = ""

        if embed_desc:
            embeds.append(simple("TOP_MEMBERS_BY_LEVEL_TEXT"))

        if not embeds:
            return await ctx.send(content["EMPTY_LEADERBOARD"])
        if len(embeds) < 2:
            return await ctx.send(embed=embeds[0])

        paginator = Paginator(
            self.bot, ctx, style=PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds=embeds
        )
        await paginator.start()

    @staticmethod
    def _get_embed(ctx: SlashContext, embed_color: int, embed_desc: str, content: dict, key: str):
        embed = Embed(
            title=content[key],
            description=embed_desc,
            color=embed_color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(
            text=f'{content["REQUESTED_BY_TEXT"]} {ctx.author.display_name}',
            icon_url=ctx.author.avatar_url,
        )
        return embed

    @slash_subcommand(
        base="levels",
        subcommand_group="leaderboard",
        name="by_voice_time",
        description="Shows top members by time in voice channel",
    )
    @is_enabled()
    async def levels_leaderboard_by__voice__time(self, ctx: SlashContext):
        def simple(key):
            return self._get_embed(
                ctx, guild_data.configuration.embed_color, embed_desc, content, key
            )

        await ctx.defer()

        guild_data = await self.bot.get_guild_data(ctx.guild_id)
        content = get_content("LEVELS", guild_data.configuration.language)["LEADERBOARD"]
        embeds = []
        embed_desc = ""
        to_sort = [
            (user_data.id, user_data.voice_time_count)
            for user_data in guild_data.users
            if user_data.voice_time_count != 0
        ]
        to_sort.sort(key=lambda x: x[-1], reverse=True)
        level_content = get_content("FUNC_MEMBER_INFO", guild_data.configuration.language)[
            "LEVELING"
        ]
        for count, user in enumerate(to_sort, start=1):
            embed_desc += (
                f"**#{count}・<@{user[0]}>**\n╰**{content['VOICE_TIME']}:** "
                f"`{format_voice_time(user[1], level_content)}`\n"
            )

            if count % 10 == 0:
                embeds.append(simple("TOP_MEMBERS_BY_VOICE_TIME_TEXT"))
                embed_desc = ""

        if embed_desc:
            embeds.append(simple("TOP_MEMBERS_BY_VOICE_TIME_TEXT"))

        if not embeds:
            return await ctx.send(content["EMPTY_LEADERBOARD"])
        if len(embeds) < 2:
            return await ctx.send(embed=embeds[0])

        paginator = Paginator(
            self.bot, ctx, style=PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds=embeds
        )
        await paginator.start()
