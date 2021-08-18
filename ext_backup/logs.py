import discord
from discord.ext import commands



class Logs(commands.Cog, description='Логи'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True

    @commands.group(name='logs', description='', help='', invoke_without_command=True)
    async def logs(self, ctx:commands.Context):
        ...

    @logs.command(name='reset', description='', help='')
    async def reset(self, ctx:commands.Context):
        self.server[str(ctx.guild.id)]['configuration']['logs'] = {}

    @logs.command(name='list', description='', help='')
    async def list(self, ctx:commands.Context):
        content="""
        Доступные для включения логи
        1. Количество выданного опыта за голосовую активность `levels`
        2. Бан, кик, мут участников сервера `moderation`
        3. Изменение настроек бота (префикс, цвет объявлений) `bot_settings`
        4. Изменение настроек Уровней
        ...
        """

    @logs.command(name='set_channel', description='', help='')
    async def set_channel(self, ctx:commands.Context):
        logs = self.server[ctx.guild.id]['configuration'].get('logs')
        if logs is None:
            return await ctx.send('Logs are disabled on this Server')




    @logs.command(name='enable', description='', help='')
    async def enable(self, ctx:commands.Context, log_type):
        ...


    @logs.command(name='disable', description='', help='')
    async def disable(self, ctx:commands.Context, log_type):
        ...


    async def toggle_levels_voice_logs(self):
        ...


    



def setup(bot):
    bot.add_cog(Logs(bot))