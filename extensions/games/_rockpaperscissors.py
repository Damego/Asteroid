from random import choice

from discord import Embed
from discord_components import Button, ButtonStyle, Interaction




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
        self.players = [self.ctx.author.id, self.member.id]

        for round in range(self.total_rounds):
            await self.rps_run_game(round)

        winner = self.rps_winner()

        embed = Embed(title='`          Results            `',
            color=self.bot.get_embed_color(self.ctx.guild.id))
        embed.add_field(name='**Name: Rock Paper Scissors**',
                        value=f"""
                        **Players:** {self.member.display_name} vs. {self.ctx.author.display_name}
                        **Played games:** {self.total_rounds}
                        **Score:** {self.count1}:{self.count2}
                        **Winner:** {winner}
                        """
                        )
        await self.message.edit(content='Game ended!', embed=embed, components=[])


    async def rps_run_game(self, round):
        def check(interaction):
            return interaction.author.id in self.players and interaction.message.id == self.message.id

        embed = Embed(title='🪨-✂️-🧾', color=self.bot.get_embed_color(self.ctx.guild.id))
        embed.add_field(name=f'**{self.member.display_name}** vs. **{self.ctx.author.display_name}**',
                        value=f'**Score:** {self.count1}:{self.count2} \n**Game:** {round+1}/{self.total_rounds}'
                        )
        await self.message.edit(
            content=' ',
            embed=embed,
            components=[
                [
                    Button(style=ButtonStyle.gray, id='rock', emoji='🪨'),
                    Button(style=ButtonStyle.gray, id='paper', emoji='🧾'),
                    Button(style=ButtonStyle.gray, id='scissors', emoji='✂️')
                ]])

        players_choice = {}
        if self.member.bot:
            players_choice[self.member.id] = choice(['rock', 'paper', 'scissors'])
        
        while True:
            interaction = await self.bot.wait_for('button_click', check=check)
                
            if interaction.author.id in players_choice:
                await interaction.send('You already moved!')
            else:
                await interaction.respond(type=6)
                players_choice[interaction.author.id] = interaction.custom_id

            if len(players_choice) == 2:
                break

        await self.rps_add_point(players_choice)


    async def rps_add_point(self, players_choice):
        player_1_choice = players_choice[self.member.id]
        player_2_choice = players_choice[self.ctx.author.id]

        if player_1_choice == player_2_choice:
            return

        if player_1_choice == 'rock':
            if player_2_choice == 'paper':
                self.count2 += 1
                return
            self.count1 += 1
            return
        elif player_1_choice == 'paper':
            if player_2_choice == 'scissors':
                self.count2 += 1
                return
            self.count1 += 1
            return
        elif player_1_choice == 'scissors':
            if player_2_choice == 'rock':
                self.count2 += 1
                return
            self.count1 += 1
            return


    def rps_winner(self):
        if self.count1 > self.count2:
            return self.member
        elif self.count1 < self.count2:
            return self.ctx.author.display_name
        return 'Draw'

