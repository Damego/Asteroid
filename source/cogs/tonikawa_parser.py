from typing import Union

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord import Embed, Forbidden
from discord.ext import tasks
from discord_slash import Button, ButtonStyle
from utils import AsteroidBot, Cog, DiscordColors, SystemChannels


class TonikawaParser(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.hidden = True
        self.name = str(self.__class__.name)
        self.fmtm_url = "https://w1.tonikakukawaii.com/"
        self.fmtm_base_chapter_url = f"{self.fmtm_url}manga/tonikaku-kawaii-chapter-"

    @Cog.listener()
    async def on_ready(self):
        if self.bot.database.global_data is None:
            await self.bot.database.init_global_data()
        self.global_data = self.bot.database.global_data
        self.check_fmtm.start()

    # * Fly Me to The Moon -> fmtm

    async def get_last_chapter_fmtm(self):
        """Send request to the site to get html"""
        async with ClientSession() as session:
            async with session.get(self.fmtm_url) as response:
                return self.parse_main_fmtm(await response.text())

    def parse_main_fmtm(self, html: str):
        """Parse html and gets the last chapter of the manga `Fly Me to The Moon`"""
        soup = BeautifulSoup(html, "html.parser")
        widget = soup.find("div", class_="textwidget")
        data = widget.find_all("li")[0]
        url = data.find("a")["href"]
        chapter = data.text.split()[-1]
        return chapter, url

    async def get_chapter_image_fmtm(self, url: str, chapter: str):
        async with ClientSession() as session:
            async with session.get(url) as response:
                return await self.parse_chapter(await response.text(), chapter)

    async def parse_chapter(self, html: str, chapter: Union[str, int]):
        soup = BeautifulSoup(html, "html.parser")
        image = soup.find("img")
        if soup.find("h2", class_="has-text-align-center") is not None:  # Fake chapter
            return await self.get_chapter_image_fmtm(
                f"{self.fmtm_base_chapter_url}{int(chapter)-1}",
                int(chapter) - 1,  # Moving to previous chapter
            )
        return image["src"], str(chapter)

    async def send_message(self, latest_chapter: str, image_url: str):
        channel = self.bot.get_channel(SystemChannels.MANGAS_UPDATES)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(SystemChannels.MANGAS_UPDATES)
            except Forbidden:
                errors_channel = self.bot.get_channel(SystemChannels.ERRORS_CHANNEL)
                await errors_channel.send("Cannot get mangas channel!")
                return

        current_chapter = self.global_data.main.fly_me_to_the_moon_chapter
        components = [
            Button(
                label=f"Читать {chapter} главу",
                style=ButtonStyle.URL,
                url=f"{self.fmtm_base_chapter_url}{chapter}",
                emoji="📖",
            )
            for chapter in range(int(current_chapter) + 1, int(latest_chapter) + 1)
        ]

        embed = Embed(
            title="Унеси меня на луну",
            description=f"**Текущая глава {current_chapter}**\n**Новая глава {latest_chapter}**",
            color=DiscordColors.FUCHSIA,
        )
        embed.set_thumbnail(
            url="https://shogakukan-comic.jp/book-images/w400/books/9784098511563.jpg"
        )
        embed.set_author(name="Новая глава!", url=self.fmtm_url)
        embed.set_image(url=image_url)
        await channel.send(embed=embed, components=[components])

    @tasks.loop(hours=1)
    async def check_fmtm(self):
        chapter, chapter_url = await self.get_last_chapter_fmtm()
        if chapter == self.global_data.main.fly_me_to_the_moon_chapter:
            return
        image_url, parsed_chapter = await self.get_chapter_image_fmtm(chapter_url, chapter)
        if parsed_chapter == self.global_data.main.fly_me_to_the_moon_chapter:
            return
        if chapter != parsed_chapter:  # If `chapter` is a fake chapter?
            chapter = parsed_chapter

        await self.send_message(chapter, image_url)
        await self.global_data.set_fmtm_chapter(chapter)


def setup(bot):
    bot.add_cog(TonikawaParser(bot))
