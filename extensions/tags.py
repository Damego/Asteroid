from discord.ext import commands
import discord
from discord_components import Button, ButtonStyle, Interaction
from pymongo.collection import Collection

from .bot_settings import is_administrator_or_bot_owner
from ._errors import TagNotFound, ForbiddenTag
from mongobot import MongoComponentsBot



class Tags(commands.Cog, description='Теги'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🏷️'

        self.forbidden_tags = ['add', 'edit', 'list', 'remove', 'rename']

    @commands.group(name='tag', description='Показывает содержание тега и управляет тегом', help='[тег || команда]', invoke_without_command=True)
    async def tag(self, ctx, tag_name=None):
        prefix = self.bot.get_guild_prefix(ctx.guild.id)
        if tag_name is None:
            return await ctx.reply(f'Упс... А тут ничего нет! Используйте `{prefix}help Tags` для получения информации')

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is None:
            raise TagNotFound

        title = tag['title']
        description = tag['description']

        embed = discord.Embed(title=title, description=description, color=self.bot.get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @tag.command(
        name='add',
        description='Создаёт новый тег',
        help='[название тега] [заголовок]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def add(self, ctx, tag_name, *, title):
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is not None:
            return await ctx.reply('Такой тег уже существует!')

        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'title':title,
                'description':''}},
            upsert=True
        )
        await ctx.message.add_reaction('✅')


    @tag.command(
        name='edit',
        description='Добавляет описание к тегу',
        help='[название тега] [описание]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def edit(self, ctx, tag_name, *, description):
        description = f"""{description}"""
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        collection.update_one(
            {'_id':tag_name},
            {'$set':{'description':description}}
        )
        await ctx.message.add_reaction('✅')


    @tag.command(
        name='remove',
        aliases=['-'],
        description='Удаляет тег',
        help='[название тега]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def remove(self, ctx, tag_name):
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound
        collection.delete_one({'_id':tag_name})

        await ctx.message.add_reaction('✅')


    @tag.command(name='list', description='Показывает список всех тегов', help='')
    async def list(self, ctx):
        description = f""""""
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tags_cursor = collection.find({})
        
        for count, tag in enumerate(tags_cursor, start=1):
            description += f'**{count}. {tag["_id"]}**\n'
            count += 1

        embed = discord.Embed(title='Список тегов', color=self.bot.get_embed_color(ctx.guild.id))
        embed.description = description
        await ctx.send(embed=embed)


    @tag.command(
        name='rename',
        description='Меняет название тега',
        help='[название тега] [новое название тега]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def rename(self, ctx, tag_name, new_tag_name):
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        if new_tag_name in self.forbidden_tags:
            raise ForbiddenTag

        title = tag['title']
        description = tag['description']

        collection.delete_one({'_id':tag_name})
        collection.update_one(
            {'_id':new_tag_name},
            {'$set':{
                'title':title,
                'description': description
            }},
            upsert=True
            )

        await ctx.message.add_reaction('✅')


    @tag.command(
        name='raw',
        description='Выдаёт исходник описания без форматирования',
        help='[название тега]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def raw(self, ctx:commands.Context, tag_name):
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        content = tag['description']
        await ctx.reply(f'```{content}```')
        

    @commands.command(
        name='btag',
        description='Открывает меню управления тегом',
        help='[название тега]',
        usage='Только для Администрации')
    @is_administrator_or_bot_owner()
    async def btag(self, ctx:commands.Context, tag_name):
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is not None:
            embed = discord.Embed(color=self.bot.get_embed_color(ctx.guild.id))
            embed.title = tag['title']
            embed.description = tag['description']
            components = [[
                Button(style=ButtonStyle.green, label='Редактировать', id='edit_tag'),
                Button(style=ButtonStyle.red, label='Удалить', id='remove_tag'),
                Button(style=ButtonStyle.red, label='Выйти', id='exit')
            ]]
            message:discord.Message = await ctx.send(embed=embed, components=components)
        else:
            embed, message = await self.init_btag(ctx)
        
        while True:
            try:
                interaction:Interaction = await self.bot.wait_for('button_click', check=lambda res: res.user.id == ctx.author.id)
            except Exception:
                continue
            
            button_id = interaction.component.id

            if button_id == 'edit_tag':
                await self.init_btag(ctx, message)
            elif button_id == 'remove_tag':
                self.remove_tag(interaction, tag_name)
                return await message.delete(delay=5)
            elif button_id == 'exit':
                return await message.delete()
            elif button_id == 'set_title':
                embed = await self.edit_tag(ctx, interaction, 'title', message, embed)
            elif button_id == 'set_description':
                embed = await self.edit_tag(ctx, interaction, 'description', message, embed)
            elif button_id == 'save_tag':
                await self.save_tag(interaction, tag_name, embed, collection)
            elif button_id == 'get_raw':
                await self.get_raw_description(ctx, interaction, tag_name, collection)

            if not interaction.responded:
                await interaction.respond(type=6)


    async def init_btag(self, ctx, *, message:discord.Message=None):
        components = [[
            Button(style=ButtonStyle.blue, label='Заголовок', id='set_title'),
            Button(style=ButtonStyle.blue, label='Описание', id='set_description'),
            Button(style=ButtonStyle.gray, label='Получить исходник', id='get_raw'),
            Button(style=ButtonStyle.green, label='Сохранить', id='save_tag'),
            Button(style=ButtonStyle.red, label='Выйти', id='exit')
        ]]

        if message is None:
            embed = discord.Embed(title='Заголовок', description='Описание', color=self.bot.get_embed_color(ctx.guild.id))
            message:discord.Message = await ctx.send(embed=embed, components=components)
        else:
            await message.edit(components=components)
        return embed, message


    async def edit_tag(self, ctx, interaction, component, message:discord.Message, embed:discord.Embed):
        label = '`Заголовок`' if component == 'title' else '`Описание`'
        await interaction.respond(type=4, content=f'Введите {label}')
        msg = await self.bot.wait_for('message', check=lambda msg: msg.author.id == ctx.author.id)
        content = msg.content
        await msg.delete()

        if component == 'title':
            embed.title = content
        elif component == 'description':
            embed.description = content

        await message.edit(embed=embed)
        return embed

    async def save_tag(self, interaction, tag_name, embed:discord.Embed, collection:Collection):
        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'title':embed.title,
                'description':embed.description
                }
            },
            upsert=True
        )

        await interaction.respond(type=4, content=f'**Сохранено!**')


    async def get_raw_description(self, interaction, tag_name, collection:Collection):
        tag = collection.find_one({'_id':tag_name})
        if tag is not None:
            tag_description = tag.get('description')
            return await interaction.respond(content=f'```{tag_description}```')
        return await interaction.respond(content='Сохраните, чтобы получить исходник!')
            
        



def setup(bot):
    bot.add_cog(Tags(bot))
