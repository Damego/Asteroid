from asyncio import TimeoutError

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, Interaction
import genshinstats as gs
from genshinstats.errors import DataNotPublic, AccountNotFound
from genshinstats.utils import is_game_uid

from ..bot_settings import get_db, get_embed_color
from .._errors import UIDNotBinded, GenshinAccountNotFound, GenshinDataNotPublic
from .rus import *



class GenshinImpact(commands.Cog, description='Genshin Impact'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.server = get_db()


    @commands.group(
        name='genshin_impact',
        aliases=['genshin', 'gi', 'gs', 'g'],
        description='',
        help='')
    async def genshin_impact(self, ctx:commands.Context):
        ...


    @genshin_impact.command(
    name='bind',
    description='Привязывает UID',
    help='')
    async def bind_uid(self, ctx:commands.Context, uid:int):
        if is_game_uid(uid):
            user_db = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
            user_db['genshin'] = {
                'uid':uid
            }
            await ctx.reply('Вы привязали UID')
        else:
            await ctx.reply('Неверный UID')


    @genshin_impact.command(
    name='statistics',
    aliases=['stats'],
    description='Показывает игровую статистику',
    help='(UID)')
    async def statistics(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            user_db = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
            if 'genshin' not in user_db:
                raise UIDNotBinded
            uid = user_db['genshin']['uid']

        gs.set_cookie_auto('chrome')
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
            user_db = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
            if 'genshin' not in user_db:
                raise UIDNotBinded
            uid = user_db['genshin']['uid']

        gs.set_cookie_auto('chrome')
        try:
            characters = gs.get_characters(uid)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound

        embed = discord.Embed(title='Genshin Impact. Персонажи', color=get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'id: {uid}')

        for character in characters:
            name = rus_characters.get(character["name"])
            if name is None:
                name = character['name']

            embed.add_field(name=f'{name} {"⭐" * character["rarity"]}',
            value=f"""
            ┕ Уровень: `{character['level']}`
            ┕ Созвездие: `C{character['constellation']}`
            ┕ Элемент: {rus_element.get(character['element'])}
            ┕ Оружие: `{character['weapon']['name']}`
            """)
        await ctx.send(embed=embed)


    @genshin_impact.command(
    name='characters',
    aliases=['chars'],
    description='Показывает полную информацию о персонажах',
    help='(UID)')
    async def chars(self, ctx:commands.Context, uid:int=None):
        if uid is None:
            user_db = self.server[str(ctx.guild.id)]['users'][str(ctx.author.id)]
            if 'genshin' not in user_db:
                raise UIDNotBinded
            uid = user_db['genshin']['uid']

        gs.set_cookie_auto('chrome')
        #gs.set_cookie(ltuid=, ltoken='')
        try:
            characters = gs.get_characters(uid)
        except DataNotPublic:
            raise GenshinDataNotPublic
        except AccountNotFound:
            raise GenshinAccountNotFound
        
        embeds = []
        pages = len(characters)

        for _page, character in enumerate(characters, start=1):
            embed = discord.Embed(title=f'{rus_characters.get(character["name"])} {"⭐" * character["rarity"]}',
            color=get_embed_color(ctx.guild.id))
            embed.set_thumbnail(url=character['icon'])
            embed.set_footer(text=f'id: {uid}. Страница: {_page}/{pages}')
            embed.description = f"""
            ┕ <:character_exp:871389287978008616> Уровень: `{character['level']}`
            ┕ Созвездие: `C{character['constellation']}`
            ┕ Элемент: {rus_element.get(character['element'])}
            ┕ <:friendship_exp:871389291740291082> Уровень дружбы: `{character['friendship']}`
            
            **Оружие**
            ┕ Название: `{character['weapon']['name']}`
            ┕ Редкость: `{"⭐" * character['weapon']["rarity"]}`
            ┕ Тип: `{rus_weapon_type.get(character['weapon']['type'])}`
            ┕ Уровень: `{character['weapon']['level']}`
            ┕ Уровень восхождения: `{character['weapon']['ascension']}`

            **Артефакты**
            """
            for artifact in character['artifacts']:
                artifact_name = rus_artifact_name.get(artifact['name'])
                if artifact_name is None:
                    artifact_name = artifact['name']

                embed.description += f"""
                ・*{rus_artifact_type[artifact['pos_name']]}*
                ┕ Название: `{artifact_name}`
                ┕ Редкость: `{"⭐" * artifact['rarity']}`
                ┕ Уровень: `{artifact['level']}`
                """
            embeds.append(embed)
        page = 1

        # Paginator
        components = [[
            Button(style=ButtonStyle.green, label='←', id='back', disabled=True),
            Button(style=ButtonStyle.blue, label=f'1/{pages}', disabled=True),
            Button(style=ButtonStyle.green, label='→', id='next'),
        ]]
        
        message:discord.Message = await ctx.send(embed=embeds[0], components=components)
        while True:
            try:
                interaction:Interaction = await self.bot.wait_for(
                    'button_click',
                    check=lambda i: i.user.id == ctx.author.id,
                    timeout=120)
            except TimeoutError:
                await message.edit(components=[])
                return
            except Exception as e:
                print(e)
                continue
            button_id = interaction.component.id
            if button_id == 'back':
                components[0][2].disabled = False
                page -= 1
                components[0][1].label = f'{page}/{pages}'
                if page == 1:
                    components[0][0].disabled = True
                else:
                    components[0][0].disabled = False
                embed = embeds[page-1]
            elif button_id == 'next':
                components[0][0].disabled = False
                page += 1
                components[0][1].label = f'{page}/{pages}'
                if page == pages:
                    components[0][2].disabled = True
                else:
                    components[0][2].disabled = False

            try:
                await interaction.respond(type=7, embed=embeds[page-1], components=components)
            except Exception:
                print('can\'t respond')