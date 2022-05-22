from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord import Embed, Forbidden
from discord.ext import tasks
from discord_slash import Button, ButtonStyle
from utils import AsteroidBot, Cog, DiscordColors, SystemChannels


class Parsers(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.hidden = True
        self.name = str(self.__class__.name)
        self.fmtm_url = "https://w1.tonikakukawaii.com/"

    @Cog.listener()
    async def on_ready(self):
        self.global_data = await self.bot.mongo.get_global_data()
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

    async def get_chapter_image_fmtm(self, url: str):
        async with ClientSession() as session:
            async with session.get(url) as response:
                return self.parse_chapter_image_fmtm(await response.text())

    def parse_chapter_image_fmtm(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        image = soup.find("img")
        return image["src"]

    async def send_message(self, chapter_url: str, image_url: str):
        channel = self.bot.get_channel(SystemChannels.MANGAS_UPDATES)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(SystemChannels.MANGAS_UPDATES)
            except Forbidden:
                errors_channel = self.bot.get_channel(SystemChannels.ERRORS_CHANNEL)
                await errors_channel.send("Cannot get mangas channel!")
                return
        chapter = self.global_data.fly_me_to_the_moon_chapter
        components = [
            Button(
                label=f"Читать {chapter} главу",
                style=ButtonStyle.URL,
                url=chapter_url,
                emoji="📖",
            )
        ]
        embed = Embed(
            title="Унеси меня на луну",
            description=f"**Глава {chapter}**",
            color=DiscordColors.FUCHSIA,
        )
        embed.set_thumbnail(url="https://cdn.myanimelist.net/images/anime/1765/122768l.jpg")
        embed.set_author(name="Новая глава!", url=self.fmtm_url)
        embed.set_image(url=image_url)
        await channel.send(embed=embed, components=components)

    @tasks.loop(hours=1)
    async def check_fmtm(self):
        last_chapter, chapter_url = await self.get_last_chapter_fmtm()
        if last_chapter != self.global_data.fly_me_to_the_moon_chapter:
            image_url = await self.get_chapter_image_fmtm(chapter_url)
            await self.global_data.set_fmtm_chapter(last_chapter)
            await self.send_message(chapter_url, image_url)


def setup(bot):
    bot.add_cog(Parsers(bot))
