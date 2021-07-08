from discord.ext import commands
import discord
from discord_components import Button, ButtonStyle

from extensions.bot_settings import get_embed_color, get_db, get_prefix



class TagNotFound(commands.CommandError):
    pass

class ForbiddenTag(commands.CommandError):
    pass


class Tags(commands.Cog, description='Теги'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.server = get_db()
        self.aliases = ['tags', 'tag']

        self.forbidden_tags = ['add', 'edit', 'list', 'remove', 'name']

    @commands.group(name='tag', description='Показывает содержание тега и управляет тегом', help='[тег || команда]', invoke_without_command=True)
    async def tag(self, ctx, tag_name=None):
        prefix = get_prefix(ctx.guild.id)
        if tag_name is None:
            return await ctx.reply(f'Упс... А тут ничего нет! Используйте `{prefix}help Tags` для получения информации')

        if tag_name not in self.server[str(ctx.guild.id)]['tags']:
            raise TagNotFound

        title = self.server[str(ctx.guild.id)]['tags'][tag_name]['title']
        description = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']

        embed = discord.Embed(title=title, description=description, color=get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)

    @tag.command(
        name='add',
        description='Создаёт новый тег',
        help='[название тега] [заголовок]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def add(self, ctx, tag_name, *, title):
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag
            
        if not self.server[str(ctx.guild.id)]['tags']:
            self.server[str(ctx.guild.id)]['tags'] = {}

        elif tag_name in self.server[str(ctx.guild.id)]['tags']:
            return await ctx.reply('Такой тег уже существует!')

        self.server[str(ctx.guild.id)]['tags'][tag_name] = {
            'title': title,
            'description': ''
        }
        await ctx.message.add_reaction('✅')


    @tag.command(
        name='edit',
        description='Добавляет описание к тегу',
        help='[название тега] [описание]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def edit(self, ctx, tag_name, *, description):
        description = f"""{description}"""
        self.server[str(ctx.guild.id)]['tags'][tag_name]['description'] = description
        await ctx.message.add_reaction('✅')


    @tag.command(
        name='remove',
        aliases=['-'],
        description='Удаляет тег (Админ)',
        help='[название тега]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def remove(self, ctx, tag_name):
        if tag_name not in self.server[str(ctx.guild.id)]['tags']:
            raise TagNotFound

        del self.server[str(ctx.guild.id)]['tags'][tag_name]
        await ctx.message.add_reaction('✅')


    @tag.command(name='list', description='Показывает список всех тегов', help='')
    async def list(self, ctx):
        description = f""""""
        all_tags = self.server[str(ctx.guild.id)]['tags']
        
        for count, tag in enumerate(all_tags, start=1):
            description += f'**{count}. {tag}**\n'
            count += 1

        embed = discord.Embed(title='Список тегов', color=get_embed_color(ctx.guild.id))
        embed.description = description
        await ctx.send(embed=embed)


    @tag.command(
        name='name',
        description='Меняет название тега',
        help='[название тега] [новое название тега]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def name(self, ctx, tag_name, new_tag_name):
        if tag_name not in self.server[str(ctx.guild.id)]['tags']:
            raise TagNotFound
        if new_tag_name in self.forbidden_tags:
            raise ForbiddenTag

        title = self.server[str(ctx.guild.id)]['tags'][tag_name]['title']
        description = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']

        del self.server[str(ctx.guild.id)]['tags'][tag_name]

        self.server[str(ctx.guild.id)]['tags'][new_tag_name] = {
            'title': title,
            'description': description
        }

        await ctx.message.add_reaction('✅')


    @commands.command(
        name='raw',
        description='Выдаёт исходник описания без форматирования',
        help='[название тега]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def raw(self, ctx:commands.Context, tag_name):
        if tag_name not in self.server[str(ctx.guild.id)]['tags']:
            raise TagNotFound

        content = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']
        await ctx.reply(content)
        

    @commands.command(
        name='btag',
        description='Открывает меню управления тегом',
        help='[название тега]',
        usage='Только для Администрации')
    @commands.has_guild_permissions(administrator=True)
    async def btag(self, ctx, tag_name):
        if tag_name in self.forbidden_tags:
            raise ForbiddenTag

        if tag_name in self.server[str(ctx.guild.id)]['tags']:
            self.embed = discord.Embed(color=get_embed_color(ctx.guild.id))
            self.embed.title = self.server[str(ctx.guild.id)]['tags'][tag_name]['title']
            self.embed.description = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']
            components = [[
                Button(style=ButtonStyle.green, label='Редактировать', id='edit_tag'),
                Button(style=ButtonStyle.red, label='Удалить', id='remove_tag'),
                Button(style=ButtonStyle.red, label='Выйти', id='exit')
            ]]
            self.msg = await ctx.send(embed=self.embed, components=components)
        else:
            await self.create_buttons(ctx)
        
        while True:
            interaction = await self.bot.wait_for('button_click', check=lambda res: res.user.id == ctx.author.id)
            button_id = interaction.component.id

            if button_id == 'edit_tag':
                await self.create_buttons(ctx, isnew=False)
            elif button_id == 'remove_tag':
                del self.server[str(ctx.guild.id)]['tags'][tag_name]
                await self.remove_message()
                return
            elif button_id == 'exit':
                await self.remove_message()
                return
            elif button_id == 'set_title':
                await self.edit_tag(ctx, interaction, 'title')
            elif button_id == 'set_description':
                await self.edit_tag(ctx, interaction, 'description')
            elif button_id == 'save_tag':
                await self.save_tag(ctx, interaction, tag_name)
            elif button_id == 'get_raw':
                await self.get_raw_description(ctx, interaction, tag_name)

            if not interaction.responded:
                await interaction.respond(type=6)


    async def create_buttons(self, ctx, isnew=True):
        components = [[
            Button(style=ButtonStyle.blue, label='Заголовок', id='set_title'),
            Button(style=ButtonStyle.blue, label='Описание', id='set_description'),
            Button(style=ButtonStyle.gray, label='Получить исходник', id='get_raw'),
            Button(style=ButtonStyle.green, label='Сохранить', id='save_tag'),
            Button(style=ButtonStyle.red, label='Выйти', id='exit'),
        ]]

        if isnew:
            self.title = 'Заголовок'
            self.description = 'Описание'
            self.embed = discord.Embed(title=self.title, description=self.description, color=get_embed_color(ctx.guild.id))
            self.msg = await ctx.send(embed=self.embed, components=components)
        else:
            await self.msg.edit(components=components)
        

    async def remove_message(self):
        await self.msg.delete()


    async def edit_tag(self, ctx, interaction, component):
        label = '`Заголовок`' if component == 'title' else '`Описание`'
        await interaction.respond(type=4, content=f'Введите {label}')
        msg = await self.bot.wait_for('message', check=lambda msg: msg.author.id == ctx.author.id)
        content = msg.content
        await msg.delete()

        if component == 'title':
            self.embed.title = content
        elif component == 'description':
            self.embed.description = content

        await self.msg.edit(embed=self.embed)


    async def save_tag(self, ctx, interaction, tag_name):
        self.server[str(ctx.guild.id)]['tags'][tag_name] = {
            'title': self.embed.title,
            'description': self.embed.description
        }
        await interaction.respond(type=4, content=f'**Сохранено!**')


    async def get_raw_description(self, ctx, interaction, tag_name):
        try:
            content = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']
        except KeyError:
            return await interaction.respond(type=4, content=f'Сохраните, чтобы получить исходник!')
            
        await interaction.respond(type=4, content=f'```{content}```')


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, TagNotFound):
            desc = 'Тег не найден!'
        elif isinstance(error, ForbiddenTag):
            desc = 'Этот тег нельзя использовать!'
        else:
            return

        embed = discord.Embed(description = desc, color=0xED4245)
        try:
            await ctx.send(embed=embed)
        except:
            await ctx.send(desc)



def setup(bot):
    bot.add_cog(Tags(bot))
