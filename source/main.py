from os import getenv

import interactions
from core import Asteroid
from dotenv import load_dotenv
from utils.functions import load_extensions

load_dotenv()

bot = Asteroid(getenv("TOKEN"), getenv("MONGO_URL"), intents=interactions.Intents.ALL)
load_extensions(bot, "extensions")


bot.start()
