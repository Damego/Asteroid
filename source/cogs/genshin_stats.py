import datetime
from enum import IntEnum

import genshin
from discord import Embed
from discord.ext import tasks
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from utils import AsteroidBot, Cog, SystemChannels, UIDNotBinded, get_content, is_enabled
from utils.consts import DiscordColors
from utils.errors import NoData
from utils.paginator import Paginator, PaginatorStyle


class GenshinEnums(IntEnum):
    ANEMOCULUS = 66
    GEOCULUS = 131
    ELECTROCULUS = 181
    TELEPORTS = 190
    DOMAINS = 35


class GenshinStats(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = 863429526632923136
        self.name = "GenshinStats"
        self.genshin_client: genshin.GenshinClient = None  # type: ignore
        self.genshin_languages = {"ru": "ru-ru", "en-US": "en-us"}
        self.cookies = None

    @Cog.listener()
    async def on_ready(self):
        if self.bot.database.global_data is None:
            await self.bot.database.init_global_data()
        if self.genshin_client is not None:
            # on_ready was called in the runtime
            return
        global_data = self.bot.database.global_data
        self.cookies = global_data.main.genshin_cookies
        self.genshin_client = genshin.GenshinClient(self.cookies)

        self.get_genshin_daily_reward.start()

    @tasks.loop(hours=24)
    async def get_genshin_daily_reward(self):
        try:
            reward = await self.genshin_client.claim_daily_reward(lang="ru-ru")
        except genshin.AlreadyClaimed:
            print("Reward already claimed!")
            return

        embed = Embed(
            title="Награда!",
            description=f"Название: {reward.name}\nКоличество: {reward.amount} шт.",
            timestamp=datetime.datetime.utcnow(),
            color=DiscordColors.BLURPLE,
        )
        embed.set_thumbnail(url=reward.icon)
        channel = self.bot.get_channel(SystemChannels.GENSHIN_DAILY_REWARDS)
        if channel is None:
            channel = await self.bot.fetch_channel(SystemChannels.GENSHIN_DAILY_REWARDS)
        await channel.send(embed=embed)

    @slash_subcommand(
        base="genshin",
        name="bind",
        description="Bind Hoyolab UID to your account",
        base_dm_permission=False,
    )
    @is_enabled()
    async def genshin_bind(self, ctx: SlashContext, hoyolab_uid: int):
        record_card = await self.genshin_client.get_record_card(hoyolab_uid)
        if not record_card.public or not record_card.has_uid:
            raise NoData

        global_data = self.bot.database.global_data
        user_data = await global_data.get_user(ctx.author_id)

        await user_data.set_genshin_uid(hoyolab_uid=hoyolab_uid, game_uid=record_card.uid)
        content = get_content(
            "GENSHIN_BIND_COMMAND", await self.bot.get_guild_bot_lang(ctx.guild_id)
        )
        await ctx.send(content)

    @slash_subcommand(
        base="genshin",
        name="statistics",
        description="Show your statistics of Genshin Impact",
    )
    @is_enabled()
    async def genshin_statistics(self, ctx: SlashContext, uid: int = None):
        await ctx.defer()
        if uid is None:
            uid = await self.get_uid(ctx)
        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        genshin_lang = self.genshin_languages[lang]
        content = get_content("GENSHIN_STATISTICS_COMMAND", lang)
        user_data = await self.genshin_client.get_user(uid, lang=genshin_lang)
        user_explorations = reversed(user_data.explorations)
        user_stats = user_data.stats

        embed = Embed(
            title=content["EMBED_WORLD_EXPLORATION_TITLE"],
            color=await self.bot.get_embed_color(ctx.guild_id),
        )
        embed.set_footer(text=f"UID: {uid}")
        for region in user_explorations:
            if region.explored == 0.0:
                continue

            description = f'{content["EXPLORED_TEXT"]}: `{region.explored}%`'
            if region.offerings:
                for offering in region.offerings:
                    if offering.name != "Reputation":
                        description += f"\n{offering.name}: `{offering.level}`"
            if region.type == "Reputation":
                description += content["REPUTATION_LEVEL_TEXT"].format(level=region.level)

            embed.add_field(name=region.name, value=description)

        oculus_content = f"""
        <:Item_Anemoculus:870989767960059944> {content['ANEMOCULUS']}: `{user_stats.anemoculi}/{GenshinEnums.ANEMOCULUS}`
        <:Item_Geoculus:870989769570676757> {content['GEOCULUS']}: `{user_stats.geoculi}/{GenshinEnums.GEOCULUS}`
        <:Item_Electroculus:870989768387878912> {content['ELECTROCULUS']}: `{user_stats.electroculi}/{GenshinEnums.ELECTROCULUS}`
        """
        embed.add_field(name=content["COLLECTED_OCULUS_TEXT"], value=oculus_content, inline=False)
        chests_opened = f"""
        {content['COMMON_CHEST']}: `{user_stats.common_chests}`
        {content['EXQUISITE_CHEST']}: `{user_stats.exquisite_chests}`
        {content['PRECIOUS_CHEST']}: `{user_stats.precious_chests}`
        {content['LUXURIOUS_CHEST']}: `{user_stats.luxurious_chests}`
        """
        embed.add_field(name=content["CHESTS_OPENED"], value=chests_opened, inline=False)
        misc_content = f"""
        <:teleport:871385272376504341> {content['UNLOCKED_TELEPORTS']}: `{user_stats.unlocked_waypoints}/{GenshinEnums.TELEPORTS}`
        <:domains:871370995192193034> {content['UNLOCKED_DOMAINS']}: `{user_stats.unlocked_domains}/{GenshinEnums.DOMAINS}`
        """
        embed.add_field(name=content["MISC_INFO"], value=misc_content, inline=False)

        await ctx.send(embed=embed)

    @slash_subcommand(
        base="genshin",
        name="characters",
        description="Show your characters of Genshin Impact",
    )
    @is_enabled()
    async def genshin_characters(self, ctx: SlashContext, uid: int = None):
        await ctx.defer()
        if uid is None:
            uid = await self.get_uid(ctx)

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        genshin_lang = self.genshin_languages[lang]
        content = get_content("GENSHIN_CHARACTERS_COMMAND", lang)
        characters = await self.genshin_client.get_characters(uid, lang=genshin_lang)
        embeds = []
        pages = len(characters)

        for _page, character in enumerate(characters, start=1):
            embed = Embed(
                title=f'{character.name} {"⭐" * character.rarity}',
                color=await self.bot.get_embed_color(ctx.guild.id),
            )
            embed.set_thumbnail(url=character.icon)
            embed.set_footer(text=f"UID: {uid}. {_page}/{pages}")
            embed = self.get_character_info(content, embed, character)
            embeds.append(embed)

        paginator = Paginator(self.bot, ctx, PaginatorStyle.FIVE_BUTTONS_WITH_COUNT, embeds)
        await paginator.start()

    @slash_subcommand(base="genshin", name="info", description="Show account information")
    @is_enabled()
    async def genshin_info(self, ctx: SlashContext, hoyolab_uid: int = None):
        await ctx.defer()
        if hoyolab_uid is None:
            hoyolab_uid = await self.get_uid(ctx, is_game_uid=False)

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        genshin_lang = self.genshin_languages[lang]
        content = get_content("GENSHIN_INFO_COMMAND", lang)

        card = await self.genshin_client.get_record_card(hoyolab_uid, lang=genshin_lang)
        user_data = await self.genshin_client.get_user(int(card.uid), lang=genshin_lang)
        user_stats = user_data.stats

        description = f"""
        **{content['NICKNAME_TEXT']}: {card.nickname}**

        <:adventure_exp:876142502736965672> {content['ADVENTURE_RANK_TEXT']}: `{card.level}`
        <:achievements:871370992839176242> {content['ACHIEVEMENTS_TEXT']}: `{user_stats.achievements}`
        :mage: {content['CHARACTERS_TEXT']}: `{user_stats.characters}`
        <:spiral_abyss:871370970600968233> {content['SPIRAL_ABYSS_TEXT']}: `{user_stats.spiral_abyss}`
        """

        embed = Embed(
            title=content["PLAYER_INFO_TEXT"],
            description=description,
            color=await self.bot.get_embed_color(ctx.guild.id),
        )
        embed.set_footer(text=f"Hoyolab UID: {hoyolab_uid} | Game UID: {card.uid}")
        await ctx.send(embed=embed)

    async def get_uid(self, ctx: SlashContext, *, is_game_uid: bool = True) -> int:
        global_data = self.bot.database.global_data
        user_data = await global_data.get_user(ctx.author_id)

        uid = user_data.genshin.game_uid if is_game_uid else user_data.genshin.hoyolab_uid
        if uid is None:
            raise UIDNotBinded
        return uid

    @staticmethod
    def get_character_info(content: dict, embed: Embed, character: genshin.models.Character):
        character_element = (
            f"» {content['CHARACTER_VISION']}: {content['GENSHIN_CHARACTER_VISION'][character.element]}"
            if character.element
            else ""
        )
        embed.description = f"""
            {content['INFORMATION_TEXT']}
            » <:character_exp:871389287978008616> {content['CHARACTER_LEVEL']}: `{character.level}`
            » {content['CHARACTER_CONSTELLATION']}: `C{character.constellation}`
            {character_element}
            » <:friendship_exp:871389291740291082> {content['CHARACTER_FRIENDSHIP']}: `{character.friendship}`

            **{content['WEAPON_TEXT']}**
            » {content['WEAPON_NAME']}: `{character.weapon.name}`
            » {content['WEAPON_RARITY']}: `{"⭐" * character.weapon.rarity}`
            » {content['WEAPON_TYPE']}: `{character.weapon.type}`
            » {content['WEAPON_LEVEL']}: `{character.weapon.level}`
            » {content['WEAPON_ASCENSION_LEVEL']}: `{character.weapon.ascension}`
            » {content['WEAPON_REFINEMENT_LEVEL']}: `{character.weapon.refinement}`

            """
        if character.artifacts:
            embed.description += content["ARTIFACTS_TEXT"]
            for artifact in character.artifacts:
                embed.description += f"""
                ・*{content['GENSHIN_ARTIFACT_TYPE'][str(artifact.pos)]}*
                » {content['ARTIFACT_NAME']}: `{artifact.name}`
                » {content['ARTIFACT_RARITY']}: `{"⭐" * artifact.rarity}`
                » {content['ARTIFACT_LEVEL']}: `{artifact.level}`
                """

        return embed


def setup(bot):
    bot.add_cog(GenshinStats(bot))
