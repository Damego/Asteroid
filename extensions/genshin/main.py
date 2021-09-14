import discord
from discord.ext import commands
from discord_components import Interaction
import genshinstats as gs
from genshinstats.errors import DataNotPublic, AccountNotFound
from genshinstats.utils import is_game_uid

from ..bot_settings import (
    PaginatorStyle,
    PaginatorCheckButtonID,
    get_interaction
    )
from .._errors import UIDNotBinded, GenshinAccountNotFound, GenshinDataNotPublic
from .rus import *
from mongobot import MongoComponentsBot


class GenshinStats(commands.Cog, description='Genshin Impact Statistics'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = 863429526632923136


    @commands.group(
        name='genshin_impact',
        aliases=['genshin', 'gi', 'gs', 'g'],
        description='Main command for getting Genshin Impact Stats',
        help='[subcommand]',
        invoke_without_command=True)
    async def genshin_impact(self, ctx:commands.Context):
        ...


    @genshin_impact.command(
    name='bind',
    description='Bind UID',
    help='[Hoyolab UID]')
    async def bind_uid(self, ctx:commands.Context, hoyolab_uid:int):
        self._get_cookie()
        uid = gs.get_uid_from_hoyolab_uid(hoyolab_uid)

        collection  = self.bot.get_guild_users_collection(ctx.guild.id)
        collection.update_one(
            {'_id':str(ctx.author.id)},
            {'$set':{
                'genshin.hoyolab_uid':hoyolab_uid,
                'genshin.uid':uid
            }}
        )
        return await ctx.reply('You binded UID')


    @genshin_impact.command(
    name='statistics',
    aliases=['stats'],
    description='Show\'s game stats',
    help='(UID)')
    async def statistics(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            uid = self._get_UID('', ctx.guild.id, ctx.author.id)

        self._get_cookie()
        try:
            user_data = gs.get_user_stats(uid)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound
        user_explorations = user_data['explorations']
        user_stats = user_data['stats']

        embed = discord.Embed(title='Genshin Impact. World exploration', color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'UID: {uid}')

        for region in user_explorations:
            if region["explored"] == 0.0:
                continue

            content = f'Explored: `{region["explored"]}%`'
            if region['name'] == 'Dragonspine':
                content += f'\nLevel of Frostbearing Tree: `{region["level"]}`'
            else:
                if region['name'] == 'Inazuma':
                    content += f'\nLevel of Sacred Sakura\'s Favor: `{region["offerings"][0]["level"]}`'
                content += f'\nReputation level: `{region["level"]}`'
            
            embed.add_field(name=region['name'], value=content)

        oculus_content = f"""
        <:Item_Anemoculus:870989767960059944> Anemoculus: `{user_stats['anemoculi']}/66`
        <:Item_Geoculus:870989769570676757> Geoculus: `{user_stats['geoculi']}/131`
        <:Item_Electroculus:870989768387878912> Electroculus: `{user_stats['electroculi']}/151`
        """

        embed.add_field(name='Collected oculus', value=oculus_content, inline=False)

        chests_opened = f"""
        Common: `{user_stats['common_chests']}`
        Exquisite: `{user_stats['exquisite_chests']}`
        Precious: `{user_stats['precious_chests']}`
        Luxurious: `{user_stats['luxurious_chests']}`
        """

        embed.add_field(name='Chest\'s opened', value=chests_opened, inline=False)

        misc_content = f"""
        <:teleport:871385272376504341> Unlocked waypoints teleports: `{user_stats['unlocked_waypoints']}/128`
        <:domains:871370995192193034> Ulocked domains: `{user_stats['unlocked_domains']}/29`
        """

        embed.add_field(name='Разное', value=misc_content, inline=False)
        await ctx.send(embed=embed)


    @genshin_impact.command(
    name='characters_list',
    aliases=['chars_list', 'chars_ls', 'cl'],
    description='Show\'s characters\'s list',
    help='(UID)')
    async def characters(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            uid = self._get_UID('', ctx.guild.id, ctx.author.id)

        self._get_cookie()
        try:
            characters = gs.get_characters(uid)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound

        embed = discord.Embed(title='Genshin Impact. Characters', color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'UID: {uid}')

        for character in characters:
            embed.add_field(name=f'{character["name"]} {"⭐" * character["rarity"]}',
            value=f"""
            ┕ Levl: `{character['level']}`
            ┕ Constellation: `C{character['constellation']}`
            ┕ Vision: {en_element.get(character['element'])}
            ┕ Weapom: `{character['weapon']['name']} {"⭐" * character['weapon']['rarity']}`
            """)
        await ctx.send(embed=embed)


    @genshin_impact.command(
    name='characters',
    aliases=['chars'],
    description='Shows full statistics about every character',
    help='(UID)')
    async def chars(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            uid = self._get_UID('', ctx.guild.id, ctx.author.id)
            
        self._get_cookie()
        try:
            characters = gs.get_characters(uid)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound
        
        embeds = []
        pages = len(characters)

        for _page, character in enumerate(characters, start=1):
            embed = discord.Embed(title=f'{character["name"]} {"⭐" * character["rarity"]}',
            color=self.bot.get_embed_color(ctx.guild.id))
            embed.set_thumbnail(url=character['icon'])
            embed.set_footer(text=f'UID: {uid}. Page: {_page}/{pages}')
            embed = self.get_character_info(embed, character)
            embeds.append(embed)

        page = 1
        components = PaginatorStyle.style2(pages)
        
        message = await ctx.send(embed=embeds[0], components=components)
        while True:
            interaction:Interaction = await get_interaction(self.bot, ctx, message)
            if interaction is None:
                return

            button_id = interaction.component.id
            paginator = PaginatorCheckButtonID(components, pages)
            page = paginator._style2(button_id, page)
            embed = embeds[page-1]

            try:
                await interaction.respond(type=7, embed=embed, components=components)
            except Exception:
                print('can\'t respond')

    @genshin_impact.command(
    name='info',
    description='Show account information',
    help='(Hoyolab UID)')
    async def info(self, ctx:commands.Context, hoyolab_uid:int=None):
        if hoyolab_uid is None:
            hoyolab_uid = self._get_UID('hoyolab', ctx.guild.id, ctx.author.id)

        self._get_cookie()
        card = gs.get_record_card(hoyolab_uid)
        user_data = gs.get_user_stats(int(card['game_role_id']))
        user_stats = user_data['stats']

        content = f"""
        **Nickname: {card['nickname']}**

        <:adventure_exp:876142502736965672> Rank of Adventure: `{card['level']}`
        <:achievements:871370992839176242> Achievements: `{user_stats['achievements']}`
        :mage: Characters: `{user_stats['characters']}`
        <:spiral_abyss:871370970600968233> Spiral Abyss: `{user_stats['spiral_abyss']}`
        """

        embed = discord.Embed(title='Information about player', description=content, color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'Hoyolab UID: {hoyolab_uid}')
        await ctx.send(embed=embed)


    def _get_cookie(self):
        gs.set_cookie(ltuid=147861638, ltoken='3t3eJHpFYrgoPdpLmbZWnfEbuO3wxUvIX7VkQXsU')

    def _get_UID(self, uid_type:str, guild_id:int, author_id:int):
        collection = self.bot.get_guild_users_collection(guild_id)
        user_genshin = collection.find_one({'_id':str(author_id)}).get('genshin')
        if user_genshin is None:
            raise UIDNotBinded

        if uid_type == 'hoyolab':
            uid = user_genshin.get('hoyolab_uid')
        else:
            uid = user_genshin.get('uid')

        if uid is None:
            raise UIDNotBinded
        return uid

    def get_character_info(self, embed:discord.Embed, character):
        embed.description = f"""
            **Information**
            » <:character_exp:871389287978008616> Level: `{character['level']}`
            » Constellation: `C{character['constellation']}`
            » Vision: {en_element.get(character['element'])}
            » <:friendship_exp:871389291740291082> Friendship level: `{character['friendship']}`
            
            **Weapon**
            » Name: `{character['weapon']['name']}`
            » Rarity: `{"⭐" * character['weapon']["rarity"]}`
            » Type: `{character['weapon']['type']}`
            » Level: `{character['weapon']['level']}`
            » Level of ascension: `{character['weapon']['ascension']}`
            » Level of refinement: `{character['weapon']['refinement']}`

            """

        if character['artifacts']:
            embed.description += '**Artifacts**'
            for artifact in character['artifacts']:
                embed.description += f"""
                ・*{en_artifact_type[artifact['pos_name']]}*
                » Name: `{artifact['name']}`
                » Rarity: `{"⭐" * artifact['rarity']}`
                » Level: `{artifact['level']}`
                """

        return embed
