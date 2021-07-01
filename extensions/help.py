import discord
from discord.ext import commands

from extensions.bot_settings import get_prefix



class Help(commands.Cog, description='Помощь'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.hidden = True
        

    @commands.command(description='Показывает это сообщение', help='[Плагин]')
    async def help(self, ctx, extension=None):
        await ctx.message.delete()

        prefix = get_prefix(ctx.guild)
        if extension is None:
            embed = discord.Embed(description='```               「📝」КОМАНДЫ:               ```', color=0x2f3136)

            for cog in self.bot.cogs:
                if not self.bot.cogs[cog].hidden:
                    embed.add_field(name=self.bot.cogs[cog].description, value=f'```{prefix}help {cog}```')
        else:
            for cog in self.bot.cogs:
                if not hasattr(self.bot.cogs[cog], 'aliases'):
                    continue
                if extension in self.bot.cogs[cog].aliases:
                    extension = cog
                    break
            else:
                if not extension in self.bot.cogs:
                    raise commands.BadArgument(f'Плагин {extension} не найден')
            cog_name = self.bot.cogs[extension].description
            embed = discord.Embed(description=f'```               「📝」{cog_name}               ```',color=0x2f3136)
            
            _commands = self.bot.cogs[extension]
            await self.out_commands(_commands, embed, prefix)
            
        await ctx.send(embed=embed, delete_after=60)


    async def out_commands(self, cmds, embed, prefix):
        if isinstance(cmds, commands.Group):
            _commands = cmds.commands
        else: _commands = cmds.get_commands()

        for _command in _commands:
            if _command.hidden:
                continue

            if _command.aliases: aliases = ', '.join(_command.aliases)
            else: aliases = 'Нет'

            embed.add_field(name=f'`{prefix}{_command} {_command.help}`', value=f'**Описание: **{_command.description}\n **Псевдонимы:** {aliases}', inline=False)

            if isinstance(_command, commands.Group):
                await self.out_commands(_command, embed, prefix)



def setup(bot):
    bot.add_cog(Help(bot))