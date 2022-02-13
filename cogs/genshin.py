from discord import Embed
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
import genshinstats as gs
from genshinstats.errors import DataNotPublic, AccountNotFound

from my_utils import (
    UIDNotBinded,
    GenshinAccountNotFound,
    GenshinDataNotPublic,
    AsteroidBot,
    get_content,
    Cog,
    is_enabled,
)
from my_utils.paginator import PaginatorStyle, Paginator


class GenshinStats(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.emoji = 863429526632923136
        self.name = "GenshinStats"

    @slash_subcommand(
        base="genshin", name="bind", description="Bind Hoyolab UID to your account"
    )
    @is_enabled()
    async def bind_uid(self, ctx: SlashContext, hoyolab_uid: int):
        self._get_cookie()
        uid = gs.get_uid_from_hoyolab_uid(hoyolab_uid)
        if uid is None:
            raise GenshinAccountNotFound

        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user( ctx.author_id)

        await user_data.set_genshin_uid(hoyolab_uid, uid)
        content = get_content("GENSHIN_BIND_COMMAND", guild_data.configuration.language)
        await ctx.send(content)

    @slash_subcommand(
        base="genshin",
        name="statistics",
        description="Show your statistics of Genshin Impact",
    )
    @is_enabled()
    async def statistics(self, ctx: SlashContext, uid: int = None):
        await ctx.defer()
        if uid is None:
            uid = await self._get_UID(ctx)

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("GENSHIN_STATISTICS_COMMAND", lang)
        genshin_data_lang = "ru-ru" if lang == "Russian" else "en-us"

        self._get_cookie()
        try:
            user_data = gs.get_user_stats(uid, lang=genshin_data_lang)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound

        user_explorations = reversed(user_data["explorations"])
        user_stats = user_data["stats"]

        embed = Embed(
            title=content["EMBED_WORLD_EXPLORATION_TITLE"],
            color=await self.bot.get_embed_color(ctx.guild_id),
        )
        embed.set_footer(text=f"UID: {uid}")

        for region in user_explorations:
            if region["explored"] == 0.0:
                continue

            description = f'{content["EXPLORED_TEXT"]}: `{region["explored"]}%`'
            if region["name"] == content["Dragonspine"]:
                description += content["FROSTBEARING_TREE_LEVEL_TEXT"].format(
                    level=region["level"]
                )
            elif region["name"] == content["Inazuma"]:
                description += content["SACRED_SAKURA_LEVEL_TEXT"].format(
                    level=region["offerings"][0]["level"]
                )
            if region["type"] == "Reputation":
                description += content["REPUTATION_LEVEL_TEXT"].format(
                    level=region["level"]
                )

            embed.add_field(name=region["name"], value=description)

        oculus_content = f"""
        <:Item_Anemoculus:870989767960059944> {content['ANEMOCULUS']}: `{user_stats['anemoculi']}/66`
        <:Item_Geoculus:870989769570676757> {content['GEOCULUS']}: `{user_stats['geoculi']}/131`
        <:Item_Electroculus:870989768387878912> {content['ELECTROCULUS']}: `{user_stats['electroculi']}/181`
        """

        embed.add_field(
            name=content["COLLECTED_OCULUS_TEXT"], value=oculus_content, inline=False
        )

        chests_opened = f"""
        {content['COMMON_CHEST']}: `{user_stats['common_chests']}`
        {content['EXQUISITE_CHEST']}: `{user_stats['exquisite_chests']}`
        {content['PRECIOUS_CHEST']}: `{user_stats['precious_chests']}`
        {content['LUXURIOUS_CHEST']}: `{user_stats['luxurious_chests']}`
        """

        embed.add_field(
            name=content["CHESTS_OPENED"], value=chests_opened, inline=False
        )

        misc_content = f"""
        <:teleport:871385272376504341> {content['UNLOCKED_TELEPORTS']}: `{user_stats['unlocked_waypoints']}/168`
        <:domains:871370995192193034> {content['UNLOCKED_DOMAINS']}: `{user_stats['unlocked_domains']}/33`
        """

        embed.add_field(name=content["MISC_INFO"], value=misc_content, inline=False)
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="genshin",
        name="characters_list",
        description="Show your characters list of Genshin Impact",
    )
    @is_enabled()
    async def characters(self, ctx: SlashContext, uid: int = None):
        await ctx.defer()
        if uid is None:
            uid = await self._get_UID(ctx)

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("GENSHIN_CHARACTERS_LIST_COMMAND", lang)
        chars_vision_content = get_content("GENSHIN_CHARACTERS_COMMAND", lang)[
            "GENSHIN_CHARACTER_VISION"
        ]
        _lang = "ru-ru" if lang == "ru" else "en-us"

        self._get_cookie()
        try:
            characters = gs.get_characters(uid, lang=_lang)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound

        embed = Embed(
            title=content["EMBED_GENSHIN_CHARACTERS_LIST_TITLE"],
            color=await self.bot.get_embed_color(ctx.guild.id),
        )
        embed.set_footer(text=f"UID: {uid}")

        for character in characters:
            embed.add_field(
                name=f'{character["name"]} {"⭐" * character["rarity"]}',
                value=f"""
            ┕ {content['CHARACTER_LEVEL']}: `{character['level']}`
            ┕ {content['CHARACTER_CONSTELLATION']}: `C{character['constellation']}`
            ┕ {content['CHARACTER_VISION']}: {chars_vision_content[character['element']]}
            ┕ {content['CHARACTER_WEAPON']}: `{character['weapon']['name']} {"⭐" * character['weapon']['rarity']}`
            """,
            )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base="genshin",
        name="characters",
        description="Show your characters of Genshin Impact",
    )
    @is_enabled()
    async def chars(self, ctx: SlashContext, uid: int = None):
        await ctx.defer()
        if uid is None:
            uid = await self._get_UID(ctx)

        self._get_cookie()

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("GENSHIN_CHARACTERS_COMMAND", lang)
        _lang = "ru-ru" if lang == "ru" else "en-us"

        try:
            characters = gs.get_characters(uid, lang=_lang)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound

        embeds = []
        pages = len(characters)

        for _page, character in enumerate(characters, start=1):
            embed = Embed(
                title=f'{character["name"]} {"⭐" * character["rarity"]}',
                color=await self.bot.get_embed_color(ctx.guild.id),
            )
            embed.set_thumbnail(url=character["icon"])
            embed.set_footer(text=f"UID: {uid}. {_page}/{pages}")
            embed = self.get_character_info(content, embed, character)
            embeds.append(embed)

        paginator = Paginator(
            self.bot, ctx, PaginatorStyle.TWO_BUTTONS, embeds
        )
        await paginator.start()

    @slash_subcommand(
        base="genshin", name="info", description="Show account information"
    )
    @is_enabled()
    async def info(self, ctx: SlashContext, hoyolab_uid: int = None):
        await ctx.defer()
        if hoyolab_uid is None:
            hoyolab_uid = await self._get_UID(ctx, is_game_uid=False)

        self._get_cookie()
        card = gs.get_record_card(hoyolab_uid)
        if card is None:
            raise GenshinAccountNotFound

        user_data = gs.get_user_stats(int(card["game_role_id"]))
        user_stats = user_data["stats"]

        lang = await self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content("GENSHIN_INFO_COMMAND", lang)

        description = f"""
        **{content['ADVENTURE_RANK_TEXT']}: {card['nickname']}**

        <:adventure_exp:876142502736965672> {content['ADVENTURE_RANK_TEXT']}: `{card['level']}`
        <:achievements:871370992839176242> {content['ACHIEVEMENTS_TEXT']}: `{user_stats['achievements']}`
        :mage: {content['CHARACTERS_TEXT']}: `{user_stats['characters']}`
        <:spiral_abyss:871370970600968233> {content['SPIRAL_ABYSS_TEXT']}: `{user_stats['spiral_abyss']}`
        """

        embed = Embed(
            title=content["PLAYER_INFO_TEXT"],
            description=description,
            color=await self.bot.get_embed_color(ctx.guild.id),
        )
        embed.set_footer(text=f"Hoyolab UID: {hoyolab_uid}")
        await ctx.send(embed=embed)

    def _get_cookie(self):
        gs.set_cookie(
            ltuid=147861638, ltoken="3t3eJHpFYrgoPdpLmbZWnfEbuO3wxUvIX7VkQXsU"
        )

    async def _get_UID(self, ctx: SlashContext, *, is_game_uid: bool = True):
        guild_data = await self.bot.mongo.get_guild_data(ctx.guild_id)
        user_data = await guild_data.get_user(ctx.author_id)

        uid = user_data.genshin_uid if is_game_uid else user_data.hoyolab_uid
        if uid is None:
            raise UIDNotBinded
        return uid

    def get_character_info(self, content: dict, embed: Embed, character: dict):
        embed.description = f"""
            {content['INFORMATION_TEXT']}
            » <:character_exp:871389287978008616> {content['CHARACTER_LEVEL']}: `{character['level']}`
            » {content['CHARACTER_CONSTELLATION']}: `C{character['constellation']}`
            » {content['CHARACTER_VISION']}: {content['GENSHIN_CHARACTER_VISION'][character['element']]}
            » <:friendship_exp:871389291740291082> {content['CHARACTER_FRIENDSHIP']}: `{character['friendship']}`
            
            **{content['WEAPON_TEXT']}**
            » {content['WEAPON_NAME']}: `{character['weapon']['name']}`
            » {content['WEAPON_RARITY']}: `{"⭐" * character['weapon']["rarity"]}`
            » {content['WEAPON_TYPE']}: `{character['weapon']['type']}`
            » {content['WEAPON_LEVEL']}: `{character['weapon']['level']}`
            » {content['WEAPON_ASCENSION_LEVEL']}: `{character['weapon']['ascension']}`
            » {content['WEAPON_REFINEMENT_LEVEL']}: `{character['weapon']['refinement']}`

            """

        if character["artifacts"]:
            embed.description += content["ARTIFACTS_TEXT"]
            for artifact in character["artifacts"]:
                embed.description += f"""
                ・*{content['GENSHIN_ARTIFACT_TYPE'][artifact['pos_name']]}*
                » {content['ARTIFACT_NAME']}: `{artifact['name']}`
                » {content['ARTIFACT_RARITY']}: `{"⭐" * artifact['rarity']}`
                » {content['ARTIFACT_LEVEL']}: `{artifact['level']}`
                """

        return embed


def setup(bot):
    bot.add_cog(GenshinStats(bot))
