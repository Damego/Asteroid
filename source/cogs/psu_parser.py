"""
Parser for site http://www.psu.ru/
"""

from dataclasses import asdict, dataclass
from threading import Thread
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

    @tasks.loop(hours=3)
    async def main(self):
        data: Dict[str, Direction] = await self.get_results()
        previous_data: Dict[str, Direction] = await self.get_previous_results()
        if previous_data is None:
            return await self.update_database(data)

        embed = Embed(
            title="ПГНИУ",
            description="**Место в конкурсе учётом того, что люди подали оригинал и согласие на зачисление**",
            color=0xC62E3E,
        )

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

    def thread_parse(html: str, result: list):
        result.append(BeautifulSoup(html, "html.parser"))

    async def parse(self, html: str):
        result = []
        thread = Thread(
            target=self.thread_parse, args=(html, result)
        )  # Use threads because it takes more 20 seconds
        thread.start()
        while not result:
            pass
        soup = result[0]
        fonts = soup.find_all("font", string=self.SNILS)
        data = {}
        for font in fonts:
            pos = font.parent.parent.find("td").text
            table = font.parent.parent.parent
            article = table.parent  # To get name and code
            direction_name = article.find("h2").find_all("span")[2].text
            count = 0
            trs = table.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                _pos = tds[0].text
                if not _pos.isdigit():  # Skip word `Общий конкурс`
                    continue
                if _pos == pos:
                    break
                if tds[2].text == "+" and tds[3].text == "+":
                    count += 1
            code = article.find("a")["name"]
            data[code] = Direction(name=direction_name, position=count + 1)
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
