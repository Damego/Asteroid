from discord.ext import commands
from discord.ext.commands import Context
import discord
from discord_components import Button, ButtonStyle, Interaction
from pymongo.collection import Collection

from .bot_settings import is_administrator_or_bot_owner
from ._errors import TagNotFound, ForbiddenTag, NotTagOwner
from mongobot import MongoComponentsBot



class Tags(commands.Cog, description='Tags'):
    def __init__(self, bot:MongoComponentsBot):
        self.bot = bot
        self.hidden = False
        self.emoji = '🏷️'

        self.forbidden_tags = ['add', 'edit', 'list', 'remove', 'rename', 'create', 'new']

    @commands.group(
        name='tag',
        description='Open tag',
        help='[tag || subcommand]',
        invoke_without_command=True)
    async def tag(self, ctx: Context, tag_name=None):
        if tag_name is None:
            return await ctx.reply(f'Use `{ctx.prefix}tag [tag || subcommand]`')
        tag_name = tag_name.lower()

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is None:
            raise TagNotFound

        title = tag['title']
        description = tag['description']
        author_id = tag['author_id']
        author = ctx.guild.get_member(author_id)

        embed = discord.Embed(title=title, description=description, color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_footer(text=f'Author of tag: {author}')
        await ctx.send(embed=embed)


    @tag.command(
        name='add',
        aliases=['create', 'new'],
        description='Create new tag',
        help='[tag name] [title]',
        usage='Everyone can use Tags on this server')
    async def add(self, ctx, tag_name, *, title):
        tag_name = tag_name.lower()
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is not None:
            return await ctx.reply('Tag already exists!')

        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                'title':title,
                'description':'',
                'author_id':ctx.author.id}},
            upsert=True
        )
        await ctx.message.add_reaction('✅')


    @tag.command(
        name='edit',
        description='Adds description for tag',
        help='[tag name] [description]',
        usage='Everyone can use Tags on this server')
    async def edit(self, ctx, tag_name, *, description):
        tag_name = tag_name.lower()
        description = f"""{description}"""
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        author_id = tag['author_id']
        if ctx.author.id not in [author_id, 143773579320754177]:
            raise NotTagOwner

        collection.update_one(
            {'_id':tag_name},
            {'$set':{'description':description}}
        )
        await ctx.message.add_reaction('✅')


    @tag.command(
        name='remove',
        aliases=['-'],
        description='Delete tag',
        help='[tag name]',
        usage='Everyone can use Tags on this server')
    async def remove(self, ctx, tag_name):
        tag_name = tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound
        
        author_id = tag['author_id']
        if ctx.author.id not in [author_id, 143773579320754177]:
            raise NotTagOwner

        collection.delete_one({'_id':tag_name})

        await ctx.message.add_reaction('✅')


    @tag.command(name='list', description='Shows list of tags', help='')
    async def list(self, ctx):
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


    @tag.command(
        name='rename',
        description='Change tag name',
        help='[tag name] [new tag name]',
        usage='Everyone can use Tags on this server')
    async def rename(self, ctx, tag_name, new_tag_name):
        tag_name = tag_name.lower()
        new_tag_name = new_tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        author_id = tag['author_id']
        if ctx.author.id not in [author_id, 143773579320754177]:
            raise NotTagOwner

        if new_tag_name in self.forbidden_tags:
            raise ForbiddenTag


        collection.update_one(
            {'_id':tag_name},
            {'$set':{
                '_id':new_tag_name
                }
            },
            upsert=True
            )

        await ctx.message.add_reaction('✅')


    @tag.command(
        name='raw',
        description='Show raw tag description',
        help='[tag name]',
        usage='Everyone can use Tags on this server')
    async def raw(self, ctx:commands.Context, tag_name):
        tag_name = tag_name.lower()
        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})
        if tag is None:
            raise TagNotFound

        content = tag['description']
        await ctx.reply(f'```{content}```')
        

    @commands.command(
        name='btag',
        description='Open control tag menu',
        help='[tag name]',
        usage='Everyone can use Tags on this server')
    async def btag(self, ctx:commands.Context, tag_name):
        tag_name = tag_name.lower()
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        collection = self.bot.get_guild_tags_collection(ctx.guild.id)
        tag = collection.find_one({'_id':tag_name})

        if tag is not None:
            author_id = tag['author_id']
            if ctx.author.id not in [author_id, 143773579320754177]:
                raise NotTagOwner

            embed = discord.Embed(color=self.bot.get_embed_color(ctx.guild.id))
            embed.title = tag['title']
            embed.description = tag['description']
            components = [[
                Button(style=ButtonStyle.green, label='Edit', id='edit_tag'),
                Button(style=ButtonStyle.red, label='Delete', id='remove_tag'),
                Button(style=ButtonStyle.red, label='Exit', id='exit')
            ]]
            message:discord.Message = await ctx.send(embed=embed, components=components)
        else:
            embed, message = await self.init_btag(ctx)
        
        while True:
            try:
                interaction:Interaction = await self.bot.wait_for(
                    'button_click',
                    check=lambda res: res.user.id == ctx.author.id and message.id == res.message.id
                    )
            except Exception as e:
                print('TAG ERROR:', e)
                continue
            
            button_id = interaction.custom_id

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
                await self.get_raw_description(interaction, embed)

            if not interaction.responded:
                await interaction.respond(type=6)


    async def init_btag(self, ctx, message:discord.Message=None):
        components = [[
            Button(style=ButtonStyle.blue, label='Title', id='set_title'),
            Button(style=ButtonStyle.blue, label='Description', id='set_description'),
            Button(style=ButtonStyle.gray, label='Get raw', id='get_raw'),
            Button(style=ButtonStyle.green, label='Save', id='save_tag'),
            Button(style=ButtonStyle.red, label='Exit', id='exit')
        ]]

        if message is None:
            embed = discord.Embed(title='Tag title', description='Tag description', color=self.bot.get_embed_color(ctx.guild.id))
            message:discord.Message = await ctx.send(embed=embed, components=components)
            return embed, message
        else:
            await message.edit(components=components)
        


    async def edit_tag(self, ctx, interaction, component, message:discord.Message, embed:discord.Embed):
        label = '`Tag title`' if component == 'title' else '`Tag description`'
        await interaction.respond(type=4, content=f'Input {label}')
        msg = await self.bot.wait_for('message', check=lambda msg: msg.author.id == ctx.author.id)
        content = msg.content

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
                'description':embed.description,
                'author_id':interaction.author.id
                }
            },
            upsert=True
        )

        await interaction.respond(type=4, content=f'**Saved!**')


    async def get_raw_description(self, interaction, embed:discord.Embed):
        tag_description = embed.description
        return await interaction.respond(content=f'```{tag_description}```')
            
        



def setup(bot):
    bot.add_cog(Tags(bot))
