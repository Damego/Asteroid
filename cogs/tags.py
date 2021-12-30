import asyncio

from discord import Embed, Message
from discord_slash import SlashContext
from discord_slash.cog_ext import cog_subcommand as slash_subcommand
from discord_slash_components_bridge import ComponentMessage, ComponentContext
from discord_components import Button, ButtonStyle
from pymongo.collection import Collection

from my_utils import AsteroidBot, is_administrator_or_bot_owner, get_content, Cog, is_enabled
from my_utils.errors import TagNotFound, NotTagOwner


class Tags(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.hidden = False
        self.name = 'Tags'

    @slash_subcommand(
        base='tag',
        name='open',
        description='Open tag'
    )
    @is_enabled()
    async def open_tag(self, ctx: SlashContext, tag_name: str, hidden: bool = False):
        tag_name = self.convert_tag_name(tag_name)

        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        tag = collection.find_one({'_id': tag_name})
        if tag is None:
            raise TagNotFound

        if tag.get('is_embed') is False:
            return await ctx.send(tag['description'])

        embed = Embed(
            title=tag['title'],
            description=tag['description'],
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        if not hidden:
            return await ctx.send(embed=embed)
        await ctx.send('✅', hidden=True)
        await ctx.channel.send(embed=embed)

    @slash_subcommand(
        base='tag',
        name='add',
        description='Create new tag'
    )
    @is_enabled()
    async def create_new_tag(self, ctx: SlashContext, tag_name: str, *, tag_content: str):
        tag_name = self.convert_tag_name(tag_name)

        self._is_can_manage_tags(ctx)

        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('TAG_ADD_COMMAND', lang)

        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        tag = collection.find_one({'_id': tag_name})

        if tag is not None:
            return await ctx.send(content['TAG_ALREADY_EXISTS_TEXT'])

        collection.update_one(
            {'_id': tag_name},
            {
                '$set': {
                    'is_embed': False,
                    'title': 'No title',
                    'description': tag_content,
                    'author_id': ctx.author.id
                    }
                },
            upsert=True
        )
        await ctx.send(content=content['TAG_CREATED_TEXT'].format(tag_name=tag_name))

    @slash_subcommand(
        base='tag',
        name='remove',
        description='Removes tag'
    )
    @is_enabled()
    async def tag_remove(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound
        self._is_can_manage_tags(ctx, tag)

        content = get_content('TAG_REMOVE_COMMAND', lang=self.bot.get_guild_bot_lang(ctx.guild_id))
        collection.delete_one({'_id': tag_name})
        await ctx.send(content['TAG_REMOVED_TEXT'].format(tag_name=tag_name))

    @slash_subcommand(
        base='tag',
        name='list',
        description='Shows list of exists tags'
    )
    @is_enabled()
    async def tag_list(self, ctx: SlashContext):
        description = ''
        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('FUNC_TAG_LIST', lang)
        tags_cursor = collection.find({})
        
        for count, tag in enumerate(tags_cursor, start=1):
            description += f'**{count}. {tag["_id"]}**\n'
            count += 1
        if description == '':
            description = content['NO_TAGS_TEXT']

        embed = Embed(
            title=content['TAGS_LIST_TEXT'].format(server=ctx.guild.name),
            description=description,
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        await ctx.send(embed=embed)

    @slash_subcommand(
        base='tag',
        name='rename',
        description='Renames tag\'s name'
    )
    @is_enabled()
    async def rename(self, ctx: SlashContext, tag_name: str, new_tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        new_tag_name = self.convert_tag_name(new_tag_name)
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('TAG_RENAME_TAG', lang)

        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx, tag)

        if tag.get('is_embed'):
            data = {
                'is_embed': True,
                'title': tag['title'],
                'description': tag['description'],
                'author_id': tag['author_id']
            }
        else:
            data = {
                'is_embed': False,
                'title': 'No title',
                'description': tag['description'],
                'author_id': tag['author_id']
            }

        collection.delete_one({'_id': tag_name})
        collection.update_one(
            {'_id': new_tag_name},
            {'$set': data},
            upsert=True
        )

        await ctx.send(
            content['TAG_RENAMED_TEXT'].format(
                tag_name=tag_name,
                new_tag_name=new_tag_name
            )
        )

    @slash_subcommand(
        base='tag',
        name='raw',
        description='Show raw tag description'
    )
    @is_enabled()
    async def raw(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        tag = collection.find_one({'_id': tag_name})
        if tag is None:
            raise TagNotFound

        self._is_can_manage_tags(ctx, tag)

        tag_content = tag['description']
        await ctx.reply(f'```{tag_content}```')

    @slash_subcommand(
        base='public',
        name='tags',
        description='Allows or disallows everyone to use tags'
    )
    @is_enabled()
    @is_administrator_or_bot_owner()
    async def allow_public_tags(self, ctx: SlashContext):
        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('PUBLIC_TAGS_COMMAND', lang)

        collection = self.bot.get_guild_cogs_collection(ctx.guild_id)
        tags = collection.find_one({'_id':'tags'})
        if tags is not None:
            current_status = tags['is_public']
            status = not current_status
        else:
            status = True

        collection.update_one(
            {'_id':'tags'},
            {'$set':{'is_public': status}},
            upsert=True
        )

        message_content = content['TAGS_PUBLIC'] if status else content['TAGS_FOR_ADMINS']
        await ctx.send(message_content)

    @slash_subcommand(
        base='tag',
        name='embed',
        description='Open embed control tag menu'
    )
    @is_enabled()
    async def tag_embed(self, ctx: SlashContext, tag_name: str):
        tag_name = self.convert_tag_name(tag_name)
        collection = self.bot.get_guild_tags_collection(ctx.guild_id)
        tag = collection.find_one({'_id': tag_name})

        self._is_can_manage_tags(ctx, tag)

        lang = self.bot.get_guild_bot_lang(ctx.guild_id)
        content = get_content('EMBED_TAG_CONTROL', lang)

        if tag is None:
            embed, message = await self.init_btag(ctx, content)
            return await self._process_interactions(ctx, message, collection, content, embed, tag_name)

        if tag.get('is_embed') is False:
            return await ctx.send(content['NOT_SUPPORTED_TAG_TYPE'])

        embed = Embed(
            title=tag['title'],
            description=tag['description'],
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        components = [
            [
                Button(style=ButtonStyle.green, label=content['EDIT_TAG_BUTTON'], id='edit_tag'),
                Button(style=ButtonStyle.red, label=content['REMOVE_TAG_BUTTON'], id='remove_tag'),
                Button(style=ButtonStyle.red, label=content['EXIT_BUTTON'], id='exit')
            ]
        ]
        message: ComponentMessage = await ctx.send(embed=embed, components=components)
        
        await self._process_interactions(ctx, message, collection, content, embed, tag_name)

    async def _process_interactions(
        self,
        ctx: SlashContext,
        message: ComponentMessage,
        collection: Collection,
        content: dict,
        embed: Embed,
        tag_name: str
        ):
        while True:
            try:
                interaction: ComponentContext = await self.bot.wait_for(
                    'button_click',
                    check=lambda inter: inter.author_id == ctx.author_id and message.id == inter.message.id,
                    timeout=600
                )
            except asyncio.TimeoutError:
                return await message.delete()
            except Exception as e:
                print('TAG ERROR:', e)
                continue

            button_id = interaction.custom_id

            if button_id == 'edit_tag':
                await self.init_btag(ctx, content, message)
            elif button_id == 'remove_tag':
                await self.remove_tag(content, interaction, collection, tag_name)
                return await message.delete(delay=5)
            elif button_id == 'exit':
                return await message.delete()
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

    async def init_btag(self, ctx: SlashContext, content: dict, message: ComponentMessage = None):
        components = [
            [
                Button(style=ButtonStyle.blue, label=content['SET_TITLE_BUTTON'], id='set_title'),
                Button(style=ButtonStyle.blue, label=content['SET_DESCRIPTION_BUTTON'], id='set_description'),
                Button(style=ButtonStyle.gray, label=content['GET_RAW_DESCRIPTION_BUTTON'], id='get_raw'),
                Button(style=ButtonStyle.green, label=content['SAVE_TAG_BUTTON'], id='save_tag'),
                Button(style=ButtonStyle.red, label=content['EXIT_BUTTON'], id='exit')
            ]
        ]

        if message is not None:
            return await message.edit(components=components)

        embed = Embed(
            title=content['TAG_TITLE_TEXT'],
            description=content['TAG_DESCRIPTION_TEXT'],
            color=self.bot.get_embed_color(ctx.guild_id)
        )
        message: ComponentMessage = await ctx.send(embed=embed, components=components)
        return embed, message

    async def edit_tag(
        self,
        ctx: SlashContext,
        content: dict,
        interaction: ComponentContext,
        component: str,
        message: ComponentMessage,
        embed: Embed
        ):
        label = content['TAG_TITLE_TEXT'] if component == 'title' else content['TAG_DESCRIPTION_TEXT']
        await interaction.send(f'{content["INPUT_TEXT"]} {label}', hidden=True)

        user_message: Message = await self.bot.wait_for(
            'message',
            check=lambda msg: msg.author.id == ctx.author_id and msg.channel.id == ctx.channel_id
        )
        message_content = user_message.content

        if component == 'title':
            embed.title = message_content
        elif component == 'description':
            embed.description = message_content

        await message.edit(embed=embed)
        return embed

    async def save_tag(self, content, interaction, tag_name, embed: Embed, collection: Collection):
        collection.update_one(
            {'_id': tag_name},
            {'$set': {
                'is_embed': True,
                'title': embed.title,
                'description': embed.description,
                'author_id': interaction.author.id
                }
            },
            upsert=True
        )

        await interaction.send(content['SAVED_TAG_TEXT'], hidden=True)

    async def get_raw_description(self, interaction: ComponentContext, embed: Embed):
        tag_description = embed.description
        await interaction.send(content=f'```{tag_description}```', hidden=True)

    async def remove_tag(
        self,
        content: dict,
        interaction: ComponentContext,
        collection: Collection,
        tag_name: str
        ):
        collection.delete_one({'_id': tag_name})
        await interaction.send(content=content['REMOVED_TAG_TEXT'], hidden=True)

    def _is_can_manage_tags(self, ctx: SlashContext, tag_data: dict = None):
        if ctx.author_id == 143773579320754177 or ctx.author.guild_permissions.manage_guild:
            return

        cogs_collection = self.bot.get_guild_cogs_collection(ctx.guild_id)
        try:
            is_public_tags = cogs_collection.find_one('tags').get('is_public')
        except KeyError:
            raise NotTagOwner

        if not is_public_tags:
            raise NotTagOwner

        if tag_data is None:
            return

        if ctx.author_id != tag_data.get('author_id'):
            raise NotTagOwner

    @staticmethod
    def convert_tag_name(tag_name: str):
        tag_name = tag_name.lower().strip()

        if ' ' in tag_name:
            tag_name = tag_name.replace(' ', '')
        if '-' in tag_name:
            tag_name = tag_name.replace('-', '')
        if '_' in tag_name:
            tag_name = tag_name.replace('_', '')

        return tag_name


def setup(bot):
    bot.add_cog(Tags(bot))
