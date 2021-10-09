from discord.ext import commands
from discord.ext.commands import Context
import discord
from discord_slash import (
    SlashContext
)
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand
)
from discord_components import Button, ButtonStyle
from discord_slash.context import ComponentContext
from discord_slash_components_bridge import ComponentMessage
from pymongo.collection import Collection

from my_utils.languages import get_content

from .settings import guild_ids
from my_utils.errors import TagNotFound, ForbiddenTag, NotTagOwner
from my_utils import AsteroidBot, is_administrator_or_bot_owner

guild_ids = guild_ids



class Tags(commands.Cog, description='Tags'):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.name = 'tags'

        self.forbidden_tags = ['add', 'description', 'list', 'remove', 'rename', 'create', 'new', 't', 'desc', 'd']

    @slash_command(
        name='tags',
        description='Open tag',
        guild_ids=guild_ids
    )
    async def tag(self, ctx: SlashContext, tag_name=None):
        if tag_name is None:
            return await ctx.reply(f'Use `{ctx.prefix}tag [tag || subcommand]`')
        tag_name = tag_name.lower()

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        title = tag.get('title')
        if title is None or title == '':
            title = 'Empty Title'
        description = tag.get('description')
        if description is None or description == '':
            description = 'Empty Description'

        embed = discord.Embed(title=title, description=description, color=self.bot.get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @slash_subcommand(
        base='tag',
        name='add',
        description='Create new tag',
        guild_ids=guild_ids
    )
    async def create_new_tag(self, ctx: SlashContext, tag_name):
        tag_name = tag_name.lower()
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        self._is_can_manage_tags(ctx)

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is not None:
            return await ctx.reply('Tag already exists!')

        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'author_id':ctx.author.id,
                'title':'Your title',
                'description':'Your description'
                }
            },
            upsert=True
        )
        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='tag',
        name='title',
        description='Set title for tag',
        guild_ids=guild_ids
    )
    async def set_tag_title(self, ctx: SlashContext, tag_name: str, *, title: str):
        tag_name = tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx)

        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'title':title
                }
            }
        )
        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='tag',
        name='description',
        description='Set description for tag',
        guild_ids=guild_ids
    )
    async def set_tag_description(self, ctx: SlashContext, tag_name, *, description):
        tag_name = tag_name.lower()
        description = f"""{description}"""
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx)

        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'description':description
                }
            }
        )
        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='tag',
        name='remove',
        description='Delete tag',
        guild_ids=guild_ids
    )
    async def remove(self, ctx: SlashContext, tag_name):
        tag_name = tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx)

        collection.delete_one({'_id':tag_name})

        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='tag',
        name='list',
        description='Shows list of tags',
        guild_ids=guild_ids
    )
    async def list(self, ctx: SlashContext):
        description = ''
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tags_cursor = collection.find({})
        
        for count, tag in enumerate(tags_cursor, start=1):
            description += f'**{count}. {tag["_id"]}**\n'
            count += 1
        if description == '':
            description = 'No tags in this server!'

        embed = discord.Embed(title='Tag list', color=self.bot.get_embed_color(ctx.guild.id))
        embed.description = description
        await ctx.send(embed=embed)


    @slash_subcommand(
        base='tag',
        name='rename',
        description='Change tag name',
        guild_ids=guild_ids
    )
    async def rename(self, ctx: SlashContext, tag_name, new_tag_name):
        tag_name = tag_name.lower()
        new_tag_name = new_tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx)

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
                }
            },
            upsert=True
        )

        await ctx.message.add_reaction('✅')


    @slash_subcommand(
        base='tag',
        name='raw',
        description='Show raw tag description',
        guild_ids=guild_ids
    )
    async def raw(self, ctx: SlashContext, tag_name):
        tag_name = tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx)

        content = tag['description']
        await ctx.reply(f'```{content}```')

    
    @slash_subcommand(
        base='public',
        name='tags',
        description='Show raw tag description',
        guild_ids=guild_ids
    )
    @is_administrator_or_bot_owner()
    async def allow_public_tags(self, ctx):
        collection = self.bot.get_guild_cogs_collection(ctx.guild_id)
        tags = collection.find_one({'_id':'tags'})
        if tags is not None:
            current_status = tags['is_public']
            status = not current_status
        else:
            status = True

        collection.update_one({'_id':'tags'}, {'$set':{'is_public':status}}, upsert=True)

        content = 'Tags now public' if status else 'Tags now only for Administators'
        await ctx.send(content)

    @slash_command(
        name='btag',
        description='Open control tag menu',
        guild_ids=guild_ids
    )
    async def btag(self, ctx: SlashContext, tag_name):
        tag_name = tag_name.lower()
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        self._is_can_manage_tags(ctx)

        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_TAGS_BTAG', lang)

        tag = collection.find_one({'_id':tag_name})

        if tag is not None:
            embed = discord.Embed(color=self.bot.get_embed_color(ctx.guild_id))
            embed.title = tag['title']
            embed.description = tag['description']
            components = [[
                Button(style=ButtonStyle.green, label=content['EDIT_TAG_BUTTON'], id='edit_tag'),
                Button(style=ButtonStyle.red, label=content['REMOVE_TAG_BUTTON'], id='remove_tag'),
                Button(style=ButtonStyle.red, label=content['EXIT_BUTTON'], id='exit')
            ]]
            message: ComponentMessage = await ctx.send(embed=embed, components=components)
        else:
            embed, message = await self.init_btag(ctx, content)
        
        while True:
            try:
                interaction: ComponentContext = await self.bot.wait_for(
                    'button_click',
                    check=lambda inter: inter.author.id == ctx.author.id and message.id == inter.message.id
                    )
            except Exception as e:
                print('TAG ERROR:', e)
                continue
            
            button_id = interaction.custom_id

            if button_id == 'edit_tag':
                await self.init_btag(ctx, content, message)
            elif button_id == 'remove_tag':
                self.remove_tag(interaction, tag_name)
                return await message.delete(delay=5)
            elif button_id == 'exit':
                await message.delete()
                return
            elif button_id == 'set_title':
                embed = await self.edit_tag(ctx, content, interaction, 'title', message, embed)
            elif button_id == 'set_description':
                embed = await self.edit_tag(ctx, content, interaction, 'description', message, embed)
            elif button_id == 'save_tag':
                await self.save_tag(content, interaction, tag_name, embed, collection)
            elif button_id == 'get_raw':
                await self.get_raw_description(interaction, embed)

            if not interaction.responded:
                await interaction.defer(edit_origin=True)

    async def init_btag(self, ctx, content, message: ComponentMessage=None):
        components = [[
            Button(style=ButtonStyle.blue, label=content['SET_TITLE_BUTTON'], id='set_title'),
            Button(style=ButtonStyle.blue, label=content['SET_DESCRIPTION_BUTTON'], id='set_description'),
            Button(style=ButtonStyle.gray, label=content['GET_RAW_DESCRIPTION_BUTTON'], id='get_raw'),
            Button(style=ButtonStyle.green, label=content['SAVE_TAG_BUTTON'], id='save_tag'),
            Button(style=ButtonStyle.red, label=content['EXIT_BUTTON'], id='exit')
        ]]

        if message is None:
            embed = discord.Embed(
                title=content['TAG_TITLE_TEXT'],
                description=content['TAG_DESCRIPTION_TEXT'],
                color=self.bot.get_embed_color(ctx.guild.id)
            )
            message: ComponentMessage = await ctx.send(embed=embed, components=components)
            return embed, message
        else:
            await message.edit(components=components)

    async def edit_tag(self, ctx, content, interaction, component, message: ComponentMessage, embed: discord.Embed):
        label = '`Tag title`' if component == 'title' else '`Tag description`'
        await interaction.send(f'{content["INPUT_TEXT"]} {label}', hidden=True)
        msg = await self.bot.wait_for('message', check=lambda msg: msg.author.id == ctx.author.id)
        content = msg.content

        if component == 'title':
            embed.title = content
        elif component == 'description':
            embed.description = content

        await message.edit(embed=embed)
        return embed

    async def save_tag(self, content, interaction, tag_name, embed: discord.Embed, collection: Collection):
        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'title':embed.title,
                'description':embed.description,
                'author_id':interaction.author.id
                }
            },
            upsert=True
        )

        await interaction.send(content['SAVED_TAG_TEXT'], hidden=True)

    async def get_raw_description(self, interaction, embed:discord.Embed):
        tag_description = embed.description
        return await interaction.send(content=f'```{tag_description}```', hidden=True)

    
    def _is_can_manage_tags(self, ctx):
        if ctx.author_id == 143773579320754177 or ctx.author.guild_permissions.administrator:
            return

        cogs_collection = self.bot.get_guild_cogs_collection(ctx.guild_id)
        try:
            is_public_tags = cogs_collection.find_one('tags').get('is_public')
        except KeyError:
            raise NotTagOwner

        if not is_public_tags:
            raise NotTagOwner


def setup(bot):
    bot.add_cog(Tags(bot))
