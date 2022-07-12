"""
Parser for site http://www.psu.ru/
"""

from dataclasses import asdict, dataclass
from typing import Dict

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord import Embed, User
from discord.ext import tasks
from utils import AsteroidBot, Cog


@dataclass
class Direction:
    name: str
    position: int


class PSUParser(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.url = "http://www.psu.ru/files/docs/priem-2022/#"
        self.directions = ["090302-13-11", "010302-13-11-67", "010302-13-11-428", "020302-13-11"]
        self.SNILS = "15759849437"
        self.session = ClientSession()
        self.current_data = {}
        self.started = False  # `on_ready` can be called multiple times during runtime
        self.previous_data = None
        self.hidden = True

    @Cog.listener()
    async def on_ready(self):
        if self.started:
            return
        if self.bot.database.global_data is None:
            await self.bot.database.init_global_data()
        self.global_data = self.bot.database.global_data
        self.main.start()
        self.started = True

    @tasks.loop(hours=6)
    async def main(self):
        data: Dict[str, Direction] = await self.get_results()
        previous_data: Dict[str, Direction] = await self.get_previous_results()
        if previous_data is None:
            return await self.update_database(data)

        embed = Embed(title="ПГНИУ", color=0xC62E3E)

        user: User = self.bot.get_user(143773579320754177)
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        for code, direction in data.items():
            current_position = direction.position
            previous_position = previous_data[code].position
            if current_position != previous_position:
                emoji = (
                    "<:_:996003879575634032>"
                    if current_position > previous_position
                    else "<:_:996003877499453460>"
                )
                description = f"{emoji} **{current_position} ({previous_position})**"
                embed.add_field(name=direction.name, value=description, inline=False)

        if embed.fields:
            await self.send_message(embed=embed)
            await self.update_database(data)

    async def get_results(self):
        async with self.session.get(self.url) as response:
            text = await response.text()
        return await self.parse(text)

    async def get_previous_results(self):
        if self.previous_data is not None:
            return self.previous_data
        raw_data: dict = await self.global_data._request.global_.get_data("psu")
        if raw_data is None:
            return
        data = {}
        for direction, info in raw_data.items():
            data[direction] = Direction(**info)
        return data

    async def parse(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        data = {}
        for direction in self.directions:
            link = soup.find("a", {"name": direction})
            article = link.parent
            direction_name = article.find("h2").find_all("span")[2].text
            about_me = article.find("font", string=self.SNILS).parent.parent
            position = about_me.find("td").text
            data[direction] = Direction(name=direction_name, position=int(position))
        return data

    async def send_message(self, embed: Embed):
        channel = self.bot.get_channel(996008478395089027)
        if channel is None:
            channel = await self.bot.fetch_channel(996008478395089027)
        await channel.send(embed=embed)

    async def update_database(self, data: Dict[str, Direction]):
        to_send = {key: asdict(value) for key, value in data.items()}
        await self.global_data._request.global_.set_data({"psu": to_send})
        self.previous_data = data


def setup(bot):
    bot.add_cog(PSUParser(bot))
