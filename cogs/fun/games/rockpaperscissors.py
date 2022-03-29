from random import choice

from discord import Embed, Member
from discord_slash import (
    SlashContext,
    ComponentMessage,
    ComponentContext,
    Button,
    ButtonStyle,
)

from utils import AsteroidBot, get_content


class RockPaperScissors:
    def __init__(
        self,
        bot: AsteroidBot,
        ctx: SlashContext,
        member: Member,
        message: ComponentMessage,
        total_rounds: int,
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
        lang = await self.bot.get_guild_bot_lang(self.guild_id)
        self.content = get_content("GAME_RPS", lang)

        for round in range(self.total_rounds):
            await self.start_round(round)

        winner = self.pick_the_winner()

        title = self.content["RESULTS_TITLE"]
        game_name = self.content["RESULTS_GAME_NAME"]
        text = self.content["RESULTS_TEXT"].format(
            self.member.display_name,
            self.ctx.author.display_name,
            self.total_rounds,
            self.count1,
            self.count2,
            winner,
        )

        embed = Embed(title=title, color=await self.bot.get_embed_color(self.guild_id))
        embed.add_field(name=game_name, value=text)
        await self.message.edit(content=" ", embed=embed, components=[])

    async def start_round(self, round):
        def check(_button_ctx):
            return (
                _button_ctx.author_id in self.players
                and _button_ctx.origin_message.id == self.message.id
            )

        players_choice = {}
        players_text = self.content["PLAYERS_TEXT"].format(
            self.member.display_name, self.ctx.author.display_name
        )
        current_score_text = self.content["CURRENT_SCORE_TEXT"].format(
            self.count1, self.count2, round + 1, self.total_rounds
        )

        embed = Embed(
            title="🪨-✂️-🧾", color=await self.bot.get_embed_color(self.guild_id)
        )
        embed.add_field(name=players_text, value=current_score_text)

        components = [
            [
                Button(style=ButtonStyle.blue, custom_id="rock", emoji="🪨"),
                Button(style=ButtonStyle.green, custom_id="paper", emoji="🧾"),
                Button(style=ButtonStyle.red, custom_id="scissors", emoji="✂️"),
            ]
        ]

        await self.message.edit(embed=embed, components=components)

        if self.member.bot:
            players_choice[self.member.id] = choice(["rock", "paper", "scissors"])

        while True:
            button_ctx: ComponentContext = await self.bot.wait_for(
                "button_click", check=check
            )

            if button_ctx.author_id in players_choice:
                made_move = self.content["MADE_MOVE_TEXT"]
                await button_ctx.send(made_move, hidden=True)
            else:
                await button_ctx.defer(ignore=True)
                players_choice[button_ctx.author_id] = button_ctx.custom_id

            if len(players_choice) == 2:
                break

        await self.rps_add_point(players_choice)

    async def rps_add_point(self, players_choice):
        player_1_choice = players_choice[self.member.id]
        player_2_choice = players_choice[self.ctx.author_id]

        if player_1_choice == player_2_choice:
            return

        if player_1_choice == "rock":
            if player_2_choice == "paper":
                self.count2 += 1
                return
            self.count1 += 1
            return
        elif player_1_choice == "paper":
            if player_2_choice == "scissors":
                self.count2 += 1
                return
            self.count1 += 1
            return
        elif player_1_choice == "scissors":
            if player_2_choice == "rock":
                self.count2 += 1
                return
            self.count1 += 1
            return

    def pick_the_winner(self):
        if self.count1 > self.count2:
            return self.member
        elif self.count1 < self.count2:
            return self.ctx.author.display_name
        return self.content["RESULTS_TIE"]
