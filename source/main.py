from os import getenv

import interactions
from core import Asteroid
from dotenv import load_dotenv
from utils.functions import load_extensions

load_dotenv()

bot = Asteroid(getenv("TOKEN"), getenv("MONGO_URL"), intents=interactions.Intents.ALL)
load_extensions(bot, "extensions")


@bot.event()
async def on_start():
    a, b = await bot.database._req.guild.find_all_documents(822119465575383102)
    print(a)


bot.start()
