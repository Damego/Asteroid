from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord import Embed, Forbidden
from discord.ext import tasks
from utils import AsteroidBot, Cog, DiscordColors, SystemChannels


class Parsers(Cog):
    def __init__(self, bot: AsteroidBot) -> None:
        self.bot = bot
        self.hidden = True
        self.name = str(self.__class__.name)

        self.fmtm_url = "https://ru.niadd.com/manga/%D0%A3%D0%BD%D0%B5%D1%81%D0%B8%20%D0%BC%D0%B5%D0%BD%D1%8F%20%D0%BD%D0%B0%20%D0%9B%D1%83%D0%BD%D1%83.html"
        self.check_fmtm.start()

    # * Fly Me to The Moon -> fmtm

    async def get_last_chapter_fmtm(self):
        """Send request to the site to get html"""
        async with ClientSession() as session:
            async with session.get(self.fmtm_url) as response:
                return self.parse_fmtm(await response.text())

    def parse_fmtm(self, html: str):
        """Parse html and gets the last chapter of the manga `Fly Me to The Moon`"""
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("div", class_="latest-asset-name").text

    def get_current_chapter_fmtm(self):
        with open("mangas.txt") as mangas_file:  # TODO: Rewrite for database
            current_chapter = mangas_file.readline()
        return current_chapter

    def write_last_chapter_fmtm(self, chapter: str):
        with open("mangas.txt", "w") as mangas_file:  # TODO: Rewrite for database
            mangas_file.write(chapter)

    async def send_message(self, current_chapter: str, last_chapter: str):
        channel = self.bot.get_channel(SystemChannels.MANGAS_UPDATES)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(SystemChannels.MANGAS_UPDATES)
            except Forbidden:
                errors_channel = self.bot.get_channel(SystemChannels.ERRORS_CHANNEL)
                await errors_channel.send("Cannot get mangas channel!")
                return
        embed = Embed(
            title="Новая глава!",
            description=f"**`{current_chapter}` -> `{last_chapter}`**",
            color=DiscordColors.FUCHSIA,
        )
        embed.set_author(name="Унеси меня на луну", url=self.fmtm_url)
        embed.set_image(
            url="https://img11.mangarussia.com/files/img/logo/20180319/201803190606147792.jpg"
        )
        await channel.send(embed=embed)

    @tasks.loop(hours=12)
    async def check_fmtm(self):
        last_chapter = await self.get_last_chapter_fmtm()
        current_chapter = self.get_current_chapter_fmtm().replace("\n", "")
        if last_chapter != current_chapter:
            self.write_last_chapter_fmtm(last_chapter)
            await self.send_message(current_chapter, last_chapter)


def setup(bot):
    bot.add_cog(Parsers(bot))
