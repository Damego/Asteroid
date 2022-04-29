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

        self.current_chapter_fmtm = None
        self.fmtm_url = "https://tonikakumanga.com/"
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
        titles = soup.find("ul", class_="menu-items").text.splitlines()
        return titles[2].split()[-1]

    def get_current_chapter_fmtm(self):
        if self.current_chapter_fmtm is not None:
            return self.current_chapter_fmtm
        with open("mangas.txt") as mangas_file:  # TODO: Rewrite for database
            self.current_chapter_fmtm = mangas_file.readline().replace("\n", "")
        return self.current_chapter_fmtm

    def write_last_chapter_fmtm(self, chapter: str):
        with open("mangas.txt", "w") as mangas_file:  # TODO: Rewrite for database
            mangas_file.write(chapter)
            self.current_chapter_fmtm = chapter

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
            url="https://static.wikia.nocookie.net/tonikaku-kawaii/images/e/e0/Volume19.png/revision/latest/scale-to-width-down/290?cb=20220128064146"
        )
        await channel.send(embed=embed)

    @tasks.loop(hours=24)
    async def check_fmtm(self):
        last_chapter = await self.get_last_chapter_fmtm()
        current_chapter = self.get_current_chapter_fmtm()
        if last_chapter != current_chapter:
            self.write_last_chapter_fmtm(last_chapter)
            await self.send_message(current_chapter, last_chapter)


def setup(bot):
    bot.add_cog(Parsers(bot))
