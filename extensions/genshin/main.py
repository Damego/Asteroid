from traceback import print_tb
import discord
from discord.ext import commands
from discord_components import Interaction
import genshinstats as gs
from genshinstats.errors import DataNotPublic, AccountNotFound
from genshinstats.utils import is_game_uid

from ..bot_settings import get_db, get_embed_color
from .._errors import UIDNotBinded, GenshinAccountNotFound, GenshinDataNotPublic
from .rus import *
from .._paginator import PaginatorStyle, PaginatorCheckButtonID, get_interaction



class GenshinImpact(commands.Cog, description='Genshin Impact'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.server = get_db()


    @commands.group(
        name='genshin_impact',
        aliases=['genshin', 'gi', 'gs', 'g'],
        description='Открывает доступ к вашей статистике игры Genshin Impact',
        help='[команда]',
        invoke_without_command=True)
    async def genshin_impact(self, ctx:commands.Context):
        ...


    @genshin_impact.command(
    name='bind',
    description='Привязывает UID',
    help='[UID]')
    async def bind_uid(self, ctx:commands.Context, uid:int):
        if is_game_uid(uid):
            user_db = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
            user_db['genshin'] = {
                'uid':uid
            }
            return await ctx.reply('Вы привязали UID')
        return await ctx.reply('Неверный UID')


    @genshin_impact.command(
    name='statistics',
    aliases=['stats'],
    description='Показывает игровую статистику',
    help='(UID)')
    async def statistics(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            uid = self._get_UID(ctx.guild.id, ctx.author.id)

        gs.set_cookie(ltuid=147861638, ltoken='3t3eJHpFYrgoPdpLmbZWnfEbuO3wxUvIX7VkQXsU')
        try:
            user_data = gs.get_user_stats(uid)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound
        user_explorations = user_data['explorations']
        user_stats = user_data['stats']

        embed = discord.Embed(title='Genshin Impact. Статистика мира', color=get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'id: {uid}')

        for region in user_explorations:
            if region["explored"] == 0.0:
                continue

            content = f'Исследовано: `{region["explored"]}%`'
            if region['name'] == 'Dragonspine':
                content += f'\nУровень Дерева Вечной Мерзлоты: `{region["level"]}`'
            else:
                content += f'\nУровень репутации: `{region["level"]}`'
            
            embed.add_field(name=rus_region.get(region['name']), value=content)

        user_stats_content = f"""
        <:achievements:871370992839176242> Достижений: `{user_stats['achievements']}`
        :mage: Персонажей: `{user_stats['characters']}`
        <:spiral_abyss:871370970600968233> Витая Бездна: `{transform_abyss_name(user_stats['spiral_abyss'])}`

        <:Item_Anemoculus:870989767960059944> Анемокулов: `{user_stats['anemoculi']}/65`
        <:Item_Geoculus:870989769570676757> Геокулов: `{user_stats['geoculi']}/131`
        <:Item_Electroculus:870989768387878912> Электрокулов: `{user_stats['electroculi']}/95`

        *Открыто сундуков*
        Обычных: `{user_stats['common_chests']}/974`
        Богатых: `{user_stats['exquisite_chests']}/687`
        Драгоценных: `{user_stats['precious_chests']}/169`
        Роскошных: `{user_stats['luxurious_chests']}/55`

        <:teleport:871385272376504341> Открыто телепортов: `{user_stats['unlocked_waypoints']}/99`
        <:domains:871370995192193034> Открыто подземелий: `{user_stats['unlocked_domains']}/28`
        """

        embed.add_field(name='Исследование мира', value=user_stats_content, inline=False)
        await ctx.send(embed=embed)


    @genshin_impact.command(
    name='characters_list',
    aliases=['chars_list', 'chars_ls', 'cl'],
    description='Показывает список персонажей',
    help='(UID)')
    async def characters(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            uid = self._get_UID(ctx.guild.id, ctx.author.id)

        gs.set_cookie(ltuid=147861638, ltoken='3t3eJHpFYrgoPdpLmbZWnfEbuO3wxUvIX7VkQXsU')
        try:
            characters = gs.get_characters(uid, lang='ru-ru')
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound

        embed = discord.Embed(title='Genshin Impact. Персонажи', color=get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'id: {uid}')

        for character in characters:
            embed.add_field(name=f'{character["name"]} {"⭐" * character["rarity"]}',
            value=f"""
            ┕ Уровень: `{character['level']}`
            ┕ Созвездие: `C{character['constellation']}`
            ┕ Элемент: {rus_element.get(character['element'])}
            ┕ Оружие: `{character['weapon']['name']} {"⭐" * character['weapon']['rarity']}`
            """)
        await ctx.send(embed=embed)


    @genshin_impact.command(
    name='characters',
    aliases=['chars'],
    description='Показывает полную информацию о персонажах',
    help='(UID)')
    async def chars(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            uid = self._get_UID(ctx.guild.id, ctx.author.id)
            
        gs.set_cookie(ltuid=147861638, ltoken='3t3eJHpFYrgoPdpLmbZWnfEbuO3wxUvIX7VkQXsU')

        try:
            characters = gs.get_characters(uid, lang='ru-ru')
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound
        
        embeds = []
        pages = len(characters)

        for _page, character in enumerate(characters, start=1):
            embed = discord.Embed(title=f'{character["name"]} {"⭐" * character["rarity"]}',
            color=get_embed_color(ctx.guild.id))
            embed.set_thumbnail(url=character['icon'])
            embed.set_footer(text=f'id: {uid}. Страница: {_page}/{pages}')

            embed.description = f"""
            **Информация**
            » <:character_exp:871389287978008616> Уровень: `{character['level']}`
            » Созвездие: `C{character['constellation']}`
            » Элемент: {rus_element.get(character['element'])}
            » <:friendship_exp:871389291740291082> Уровень дружбы: `{character['friendship']}`
            
            **Оружие**
            » Название: `{character['weapon']['name']}`
            » Редкость: `{"⭐" * character['weapon']["rarity"]}`
            » Тип: `{character['weapon']['type']}`
            » Уровень: `{character['weapon']['level']}`
            » Уровень восхождения: `{character['weapon']['ascension']}`
            » Уровень возвышения: `{character['weapon']['refinement']}`

            """

            if character['artifacts']:
                embed.description += '**Артефакты**'
                for artifact in character['artifacts']:
                    embed.description += f"""
                    ・*{rus_artifact_type[artifact['pos_name']]}*
                    » Название: `{artifact['name']}`
                    » Редкость: `{"⭐" * artifact['rarity']}`
                    » Уровень: `{artifact['level']}`
                    """

            embeds.append(embed)

        page = 1
        components = PaginatorStyle.style2(pages)
        
        message:discord.Message = await ctx.send(embed=embeds[0], components=components)
        while True:
            interaction:Interaction = await get_interaction(self.bot, ctx, message)
            if interaction is None:
                return

            button_id = interaction.component.id
            paginator = PaginatorCheckButtonID(components, pages)
            page = paginator._style1(button_id, page)
            #page = PaginatorCheckButtonID.style2(button_id, page, pages, components)
            embed = embeds[page-1]

            try:
                await interaction.respond(type=7, embed=embed, components=components)
            except Exception:
                print('can\'t respond')

    def _get_UID(self, guild_id:int, author_id:int):
            user_db = self.server[str(guild_id)]['users'][str(author_id)]
            user_genshin = user_db.get('genshin')
            if not user_genshin:
                raise UIDNotBinded
            return user_genshin['uid']