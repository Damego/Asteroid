from random import randint

from discord import Embed
from discord_components import Button, ButtonStyle, Interaction

from ..bot_settings import get_embed_color


class RockPaperScissors:
    def __init__(self, bot, ctx, member, message, total_rounds) -> None:
        self.bot = bot
        self.ctx = ctx
        self.member = member
        self.message = message
        self.total_rounds = total_rounds


    async def start_game(self):
        self.count1 = 0
        self.count2 = 0

        for round in range(self.total_rounds):
            await self.rps_run_game(round)

        winner = self.rps_winner()

        embed = Embed(title='`          ИТОГИ ИГРЫ            `')
        embed.add_field(name=f'**Название игры: Камень-ножницы-бумага**',
                        value=f"""
                        **Игроки:** {self.member.display_name} и {self.ctx.author.display_name}
                        **Количество сыгранных игр:** {self.total_rounds}
                        **Счёт:** {self.count1}:{self.count2}
                        **Победитель:** {winner}
                        """
                        )
        await self.message.edit(content='Игра закончилась!', embed=embed, components=[])


    async def rps_run_game(self, round):
        def player_1(interaction):
            return interaction.user == self.member

        def player_2(interaction):
            return interaction.user == self.ctx.author

        embed = Embed(title='🪨-✂️-🧾', color=get_embed_color(self.ctx.guild.id))
        embed.add_field(name=f'**{self.member.display_name}** VS **{self.ctx.author.display_name}**',
                        value=f'**Счёт:** {self.count1}:{self.count2} \n**Игра:** {round+1}/{self.total_rounds}'
                        )
        await self.message.edit(
            content='Идёт игра...',
            embed=embed,
            components=[
                [
                    Button(style=ButtonStyle.gray, id=1, emoji='🪨'),
                    Button(style=ButtonStyle.gray, id=2, emoji='🧾'),
                    Button(style=ButtonStyle.gray, id=3, emoji='✂️')
                ]])
                
        if self.member.bot:
            player_1_choice = str(randint(1, 3))
        else:
            player_1_interact = await self.bot.wait_for("button_click", check=player_1)
            await player_1_interact.respond(type=6)
            player_1_choice = player_1_interact.component.id
        player_2_interact = await self.bot.wait_for("button_click", check=player_2)
        await player_2_interact.respond(type=6)

        await self.rps_logic(player_1_choice, player_2_interact.component.id)



    async def rps_logic(self, player_1_choice, player_2_choice):
        """Проверяет ходы участников и даёт очко тому, кто выиграл"""
        if player_1_choice == player_2_choice:
            return
        elif player_1_choice == '1':
            if player_2_choice == '3':
                self.count1 += 1
                return
            self.count2 += 1
            return
        elif player_1_choice == '2':
            if player_2_choice == '1':
                self.count1 += 1
                return
            self.count2 += 1
            return
        elif player_1_choice == '3':
            if player_2_choice == '2':
                self.count1 += 1
                return
            self.count2 += 1
            return


    def rps_winner(self):
        """Определяет по очкам, кто в итоге победил, и возвращает победителя"""
        if self.count1 > self.count2:
            return self.member
        elif self.count1 < self.count2:
            return self.ctx.author.display_name
        return 'Ничья'

