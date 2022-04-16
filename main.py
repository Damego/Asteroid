from os import getenv

from dotenv import load_dotenv

from utils import AsteroidBot, load_localization, slash_override  # noqa: F401

load_dotenv()
load_localization()

bot = AsteroidBot(mongodb_token=getenv("MONGODB_URL"), github_token=getenv("GITHUB_TOKEN"))

bot.run(getenv("BOT_TOKEN"))
