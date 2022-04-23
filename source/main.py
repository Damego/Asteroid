from os import getenv, listdir

from dotenv import load_dotenv
from utils import AsteroidBot, load_localization, slash_override  # noqa: F401


def load_extensions(bot):
    for filename in listdir("./cogs"):
        try:
            if filename.startswith("_"):
                continue
            if filename.endswith(".py"):
                bot.load_extension(f"cogs.{filename[:-3]}")
            elif "." in filename:
                continue
            else:
                bot.load_extension(f"cogs.{filename}")
        except Exception as e:
            print(f"Extension {filename} not loaded!\nError: {e}")


load_dotenv()
load_localization()

bot = AsteroidBot(
    mongodb_token=getenv("MONGODB_URL"),
    github_token=getenv("GITHUB_TOKEN"),
    repo_name="Damego/Asteroid-Discord-Bot",
)
load_extensions(bot)

bot.run(getenv("BOT_TOKEN"))
