from random import randint

from discord import Embed, Member
from discord_slash import ButtonStyle, SlashContext, ComponentMessage
from discord_slash.utils.manage_components import (
    create_button as Button,
    create_actionrow as ActionRow,
    wait_for_component
)

from my_utils import AsteroidBot
from my_utils import get_content


class RockPaperScissors:
    def __init__(
        self,
        bot: AsteroidBot,
        ctx: SlashContext,
        member: Member,
        message: ComponentMessage,
        total_rounds: int
        ) -> None:
        self.bot = bot
        self.ctx = ctx
        self.member = member
        self.message = message
        self.total_rounds = total_rounds
        self.guild_id = ctx.guild_id


    async def start_game(self):
        self.count1 = 0
        self.count2 = 0
        self.players = [self.ctx.author_id, self.member.id]
        lang = self.bot.get_guild_bot_lang(self.guild_id)
        self.content = get_content('GAME_RPS', lang)

        for round in range(self.total_rounds):
            await self.start_round(round)

        winner = self.pick_the_winner()

        title = self.content['RESULTS_TITLE']
        game_name = self.content['RESULTS_GAME_NAME']
        text = self.content['RESULTS_TEXT'].format(
            self.member.display_name,
            self.ctx.author.display_name,
            self.total_rounds,
            self.count1,
            self.count2,
            winner
        )


        embed = Embed(title=title, color=self.bot.get_embed_color(self.guild_id))
        embed.add_field(name=game_name,value=text)
        await self.message.edit(content=' ', embed=embed, components=[])


    async def start_round(self, round):
        def check(interaction):
            return interaction.author_id in self.players

        players_choice = {}
        players_text = self.content['PLAYERS_TEXT'].format(
            self.member.display_name,
            self.ctx.author.display_name
        )
        current_score_text = self.content['CURRENT_SCORE_TEXT'].format(
            self.count1,
            self.count2,
            round+1,
            self.total_rounds
        )
        
        embed = Embed(title='🪨-✂️-🧾', color=self.bot.get_embed_color(self.guild_id))
        embed.add_field(
            name=players_text,
            value=current_score_text
        )

        components = [
            Button(style=ButtonStyle.gray, custom_id='1', emoji='🪨'),
            Button(style=ButtonStyle.gray, custom_id='2', emoji='🧾'),
            Button(style=ButtonStyle.gray, custom_id='3', emoji='✂️')
        ]
        action_row = ActionRow(*components)

        await self.message.edit(
            embed=embed,
            components=[action_row])
                
        if self.member.bot:
            players_choice[self.member.id] = str(randint(1, 3))
        
        while True:
            interaction = await wait_for_component(
                self.bot,
                messages=self.message.id,
                components=action_row, 
                check=check
            )
                
            if interaction.author_id in players_choice:
                made_move = self.content['MADE_MOVE_TEXT']
                await interaction.send(made_move)
            else:
                await interaction.defer(ignore=True)
                players_choice[interaction.author_id] = interaction.custom_id

            if len(players_choice) == 2:
                break

        await self.rps_add_point(players_choice)


    async def rps_add_point(self, players_choice):
        player_1_choice = players_choice[self.member.id]
        player_2_choice = players_choice[self.ctx.author_id]

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


    def pick_the_winner(self):
        if self.count1 > self.count2:
            return self.member
        elif self.count1 < self.count2:
            return self.ctx.author.display_name
        return self.content['RESULTS_TIE']

