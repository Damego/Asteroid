from discord.ext import commands
import discord
from discord_components import Button, ButtonStyle, DiscordComponents

from extensions.bot_settings import get_embed_color, get_db, get_prefix, get_footer_text



class Tags(commands.Cog, description='Теги'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.server = get_db()
        self.embed_footer = get_footer_text()

        self.forbidden_tags = ['add', 'edit', 'list', 'remove', 'help', 'name']

    @commands.group(name='tag', description='Показывает содержание тега и управляет тегом', help='[тег || команда]', invoke_without_command=True)
    async def tag(self, ctx, tag_name):
        if not tag_name in self.server[str(ctx.guild.id)]['tags']:
            return await ctx.reply('Такого тега не существует!')

        title = self.server[str(ctx.guild.id)]['tags'][tag_name]['title']
        description = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']

        embed = discord.Embed(title=title, description=description, color=get_embed_color(ctx.guild))
        embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @tag.command(name='add', description='Создаёт новый тег (Админ)', help='[название тега] [заголовок]')
    @commands.has_guild_permissions(administrator=True)
    async def add(self, ctx, tag_name, *, title):
        if tag_name in self.forbidden_tags:
            return await ctx.reply('Этот тег нельзя использовать!')
            
        if not self.server[str(ctx.guild.id)]['tags']:
            self.server[str(ctx.guild.id)]['tags'] = {}

        elif tag_name in self.server[str(ctx.guild.id)]['tags']:
            return await ctx.reply('Такой тег уже существует!')

        self.server[str(ctx.guild.id)]['tags'][tag_name] = {
            'title': title,
            'description': ''
        }
        await ctx.message.add_reaction('✅')


    @tag.command(name='edit', description='Добавляет описание к тегу (Админ)', help='[название тега] [описание]')
    @commands.has_guild_permissions(administrator=True)
    async def edit(self, ctx, tag_name, *, description):
        description = f"""{description}"""
        self.server[str(ctx.guild.id)]['tags'][tag_name]['description'] = description
        await ctx.message.add_reaction('✅')


    @tag.command(aliases=['-'], name='remove', description='Удаляет тег (Админ)', help='[название тега]')
    @commands.has_guild_permissions(administrator=True)
    async def remove(self, ctx, tag_name):
        del self.server[str(ctx.guild.id)]['tags'][tag_name]
        await ctx.message.add_reaction('✅')


    @tag.command(name='list', description='Показывает список всех тегов', help='')
    async def list(self, ctx):
        description = f""""""
        all_tags = self.server[str(ctx.guild.id)]['tags']
        count = 1
        for tag in all_tags:
            description += f'**{count}. {tag}**\n'
            count += 1
        embed = discord.Embed(title='Список тегов', color=get_embed_color(ctx.guild))
        embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)
        embed.description = description
        await ctx.send(embed=embed)


    @tag.command(name='help', description='Показывает список команд', help='')
    async def help(self, ctx):
        prefix = get_prefix(ctx.guild)
        cog_name = self.bot.cogs['Tags'].description
        embed = discord.Embed(color=0x2f3136)
        embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)
        embed.add_field(name='**Справочник команд**', value=f'```               「📝」{cog_name}               ```', inline=False)
        all_cmds = self.bot.cogs['Tags'].get_commands()
        for cmd in all_cmds:
            if cmd.hidden:
                continue

            if cmd.aliases: aliases = ', '.join(cmd.aliases)
            else: aliases = 'Нет'

            embed.add_field(name=f'`{prefix}{cmd} {cmd.help}`', value=f'**Описание: **{cmd.description}\n **Псевдонимы:** {aliases}', inline=False)

            if isinstance(cmd, commands.Group):
                group_cmds = cmd.commands
                for group_cmd in group_cmds:
                    if group_cmd.hidden:
                        continue
                    if group_cmd.aliases: aliases = ', '.join(cmd.aliases)
                    else: aliases = 'Нет'

                    embed.add_field(name=f'`{prefix}{group_cmd} {group_cmd.help}`', value=f'**Описание:** {group_cmd.description}\n **Псевдонимы:** {aliases}', inline=False)
        await ctx.send(embed=embed)

    @tag.command(name='name', description='Меняет название тега', help='[название тега] [новое название тега]')
    @commands.has_guild_permissions(administrator=True)
    async def name(self, ctx, tag_name, new_tag_name):
        if not tag_name in self.server[str(ctx.guild.id)]['tags']:
            return await ctx.reply('Такого тега не существует!')
        if new_tag_name in self.forbidden_tags:
            return await ctx.reply('Этот тег нельзя использовать!')
        
        title = self.server[str(ctx.guild.id)]['tags'][tag_name]['title']
        description = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']

        del self.server[str(ctx.guild.id)]['tags'][tag_name]

        self.server[str(ctx.guild.id)]['tags'][new_tag_name] = {
            'title': title,
            'description': description
        }

        await ctx.message.add_reaction('✅')


    @commands.command(name='btag', description='Открывает меню управления тегом (Админ)', help='[название тега]')
    @commands.has_guild_permissions(administrator=True)
    async def btag(self, ctx, tag_name):
        if tag_name in self.forbidden_tags:
            return await ctx.reply('Этот тег нельзя использовать!')

        if tag_name in self.server[str(ctx.guild.id)]['tags']:
            self.embed = discord.Embed(color=get_embed_color(ctx.guild))
            self.embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)
            self.embed.title = self.server[str(ctx.guild.id)]['tags'][tag_name]['title']
            self.embed.description = self.server[str(ctx.guild.id)]['tags'][tag_name]['description']
            components = [[
                Button(style=ButtonStyle.green, label='Редактировать', id='1'),
                Button(style=ButtonStyle.red, label='Удалить', id='2'),
                Button(style=ButtonStyle.red, label='Выйти', id='3')
            ]]
            self.msg = await ctx.send(embed=self.embed, components=components)
        else:
            await self.create_buttons(ctx)
        
        while True:
            interaction = await self.bot.wait_for('button_click', check=lambda res: res.user.id == ctx.author.id)
            button_id = interaction.component.id

            if button_id == '1':
                await self.create_buttons(ctx, isnew=False)
            elif button_id == '2':
                del self.server[str(ctx.guild.id)]['tags'][tag_name]
                await self.remove_message()
                return
            elif button_id == '3':
                await self.remove_message()
                return
            elif button_id == '10':
                await self.edit_tag(ctx, interaction, 'title')
            elif button_id == '11':
                await self.edit_tag(ctx, interaction, 'description')
            elif button_id == '12':
                await self.save_tag(ctx, interaction, tag_name)

            if not interaction.responded:
                await interaction.respond(type=6)


    async def create_buttons(self, ctx, isnew=True):
        components = [[
            Button(style=ButtonStyle.blue, label='Заголовок', id='10'),
            Button(style=ButtonStyle.blue, label='Описание', id='11'),
            Button(style=ButtonStyle.green, label='Сохранить', id='12'),
            Button(style=ButtonStyle.red, label='Выйти', id='3'),
        ]]

        if isnew:
            self.title = 'Заголовок'
            self.description = 'Описание'
            self.embed = discord.Embed(title=self.title, description=self.description, color=get_embed_color(ctx.guild))
            self.embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)
            self.msg = await ctx.send(embed=self.embed, components=components)
        else:
            await self.msg.edit(components=components)
        

    async def remove_message(self):
        await self.msg.delete()


    async def edit_tag(self, ctx, interaction, component):
        if component == 'title': label = '`Заголовок`'
        else: label = '`Описание`'

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



def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Tags(bot))
