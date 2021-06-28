import discord
from discord.ext import commands

from extensions.bot_settings import get_db, get_prefix, get_footer_text

server = get_db()


class Help(commands.Cog, description='Помощь'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.hidden = True
        self.embed_footer = get_footer_text()
        

    @commands.command(description='Показывает это сообщение')
    async def help(self, ctx, extension=None):
        prefix = get_prefix(ctx.guild)

        if extension is None:
            embed = discord.Embed(description='```               「📝」КОМАНДЫ:               ```', color=0x2f3136)
            embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)

            for cog in self.bot.cogs:
                if not self.bot.cogs[cog].hidden:
                    embed.add_field(name=self.bot.cogs[cog].description, value=f'```{prefix}help {cog}```')

        elif extension in self.bot.cogs:
            cog_name = self.bot.cogs[extension].description

            embed = discord.Embed(description=f'```               「📝」{cog_name}               ```',color=0x2f3136)
            embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)
            
            all_cmds = self.bot.cogs[extension].get_commands()
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
        else:
            embed = discord.Embed(title=f'Плагин `{extension}` не найден!',color=0x2f3136)
            embed.set_footer(text=self.embed_footer, icon_url=self.bot.user.avatar_url)

        await ctx.message.delete()
        await ctx.send(embed=embed, delete_after=60)



def setup(bot):
    bot.add_cog(Help(bot))