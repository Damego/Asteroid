import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle

class Games(commands.Cog, description='Игры'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False


    async def check_results(self, res1, res2):
        if res1.component.id == res2.component.id:
            return
        elif res1.component.id == '1':
            if res2.component.id == '3':
                self.count1 +=1
                return 
            self.count2 +=1
            return 
        elif res1.component.id == '2':
            if res2.component.id == '1':
                self.count1 +=1
                return 
            self.count2 +=1
            return 
        elif res1.component.id == '3':
            if res2.component.id == '2':
                self.count1 +=1
                return 
            self.count2 +=1
            return 

    async def who_won(self, ctx, res):
        if self.count1 > self.count2:
            return ctx.author.display_name
        elif self.count1 < self.count2:
            return res.user
        return 'Ничья'

    async def game(self, ctx, msg, member, game_number, quantity):
        def player_1(res):
            if res.user == ctx.author:
                return res.component.id
        def player_2(res):
            if res.user == member:
                return res.component.id

        embed = discord.Embed(title='🪨-✂️-🧾')
        embed.add_field(name=f'**{ctx.author.display_name}** VS **{member.display_name}**',
                        value=f'**Счёт:** {self.count1}:{self.count2} \n**Игра:** {game_number+1}/{quantity}'
        )
        await msg.edit(
            content=None,
            embed=embed,
            components=[
                [
                    Button(style=ButtonStyle.gray, id=1, emoji='🪨'),
                    Button(style=ButtonStyle.gray, id=2, emoji='🧾'),
                    Button(style=ButtonStyle.gray, id=3, emoji='✂️')
                ]])
        res1 = await self.bot.wait_for("button_click", check=player_1)
        res2 = await self.bot.wait_for("button_click", check=player_2)

        await self.check_results(res1, res2)

    @commands.command(description='Запускает игру Камень-ножницы-бумага', help='[ник] [кол-во игр]')
    async def rps(self, ctx, member:discord.Member, quantity:int):
        self.count1 = 0
        self.count2 = 0

        def member_agree(res):
            return member == res.user

        msg = await ctx.send(
            f"{member.mention}! {ctx.author.name} приглашает тебя в игру 🪨-✂️-🧾",
            components=[
                [
                    Button(style=ButtonStyle.green, label='Согласиться', id=1),
                    Button(style=ButtonStyle.red, label='Отказаться', id=2)
                ]])

        try:
            res = await self.bot.wait_for("button_click", check=member_agree, timeout=60)
        except Exception:
            res = None
        if res.component.id == '1':
            for game_number in range(quantity):
                await self.game(ctx, msg, member, game_number, quantity)

            winner = await self.who_won(ctx, res)

            embed = discord.Embed(title='`          ИТОГИ ИГРЫ            `')
            embed.add_field(name=f'**Игроки: {ctx.author.display_name} и {member.display_name}**',
                            value=f"""
                            **Название игры: 🪨-✂️-🧾**
                            **Количество сыгранных игр:** {quantity}
                            **Счёт:** {self.count1}:{self.count2}
                            **Победитель:** {winner}
                            """
            )
            await msg.edit(embed=embed, components=[])
        else:
            await msg.delete()
            await ctx.send(f'{res.user} отказался от игры')

def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Games(bot))